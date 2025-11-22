"""Implementação do solver de backtracking para Sudoku.

Mantém responsabilidades bem separadas para facilitar as próximas etapas do
roadmap (heurísticas, explain mode, benchmarking, outros solvers) sem precisar
reescrever a base.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional, Tuple

from core.board import Board
from core.rules import SudokuRules

from .base import Solver
from .types import StepEvent


@dataclass
class SearchMetrics:
    """Estrutura leve que armazena estatísticas da recursão."""

    explored_nodes: int = 0
    backtracks: int = 0
    max_depth: int = 0


class BacktrackingSolver(Solver):
    """Solver de Sudoku por backtracking em profundidade.

    Mantém o tabuleiro original intacto usando operações imutáveis
    (``Board.with_value``). Os ganchos auxiliares (``_select_cell`` e
    ``_ordered_candidates``) facilitam a introdução de heurísticas como MRV/LCV
    ou ordenações especiais para o Explain Mode.
    """

    def __init__(self, rules: Optional[SudokuRules] = None) -> None:
        """Cria uma instância do solver.

        Args:
            rules: Regras opcionais; usa :class:`SudokuRules` por padrão.
        """

        self._rules = rules or SudokuRules()
        self._metrics = SearchMetrics()

    def solve(self, board: Board) -> Optional[Board]:
        """
        Resolve ``board`` retornando uma nova instância de :class:`Board`.
        """

        self._metrics = SearchMetrics()
        return self._search(board)

    def solve_generator(self, board: Board) -> Iterator[StepEvent]:
        """Versão geradora: emite eventos de atribuição/backtracking."""
        self._metrics = SearchMetrics()
        yield from self._search_events(board, depth=0)

    def metrics(self) -> SearchMetrics:
        """Exibe as estatísticas coletadas na última execução."""

        return self._metrics

    def _search(self, board: Board) -> Optional[Board]:
        """DFS recursivo responsável pelo backtracking."""

        self._metrics.explored_nodes += 1
        next_cell = self._select_cell(board)
        if next_cell is None:
            return board if self._rules.is_solved(board) else None

        row, col = next_cell
        for value in self._ordered_candidates(board, row, col):
            if not self._rules.can_place(board, row, col, value):
                continue
            try:
                new_board = board.with_value(row, col, value)
            except PermissionError:
                continue
            solved = self._search(new_board)
            if solved is not None:
                return solved
        return None

    def _select_cell(self, board: Board) -> Optional[Tuple[int, int]]:
        """Seleciona a próxima célula vazia.

        A estratégia padrão caminha linha a linha, mas heurísticas futuras
        podem sobrescrever o método (ex.: MRV) mantendo o núcleo recursivo.
        """

        size = board.size()
        for row in range(size):
            for col in range(size):
                if board.get(row, col) == 0:
                    return (row, col)
        return None

    def _ordered_candidates(
        self, board: Board, row: int, col: int
    ) -> Iterator[int]:
        """Gera dígitos candidatos para ``(row, col)`` na ordem explorada."""

        size = board.size()
        for value in range(1, size + 1):
            yield value

    # ------------------------------------------------------------------ #
    # Explain Mode (eventos)
    # ------------------------------------------------------------------ #

    def _search_events(self, board: Board, depth: int) -> Iterator[StepEvent]:
        """DFS recursivo emitindo eventos de explicação."""
        self._metrics.explored_nodes += 1
        self._metrics.max_depth = max(self._metrics.max_depth, depth)

        next_cell = self._select_cell(board)
        if next_cell is None:
            yield StepEvent(
                step_type="finished",
                cell=None,
                value=0,
                candidates=None,
                reason="Puzzle resolvido",
                board=board,
                depth=depth,
            )
            return board

        row, col = next_cell
        candidates = list(self._ordered_candidates(board, row, col))

        for value in candidates:
            if not self._rules.can_place(board, row, col, value):
                continue
            try:
                new_board = board.with_value(row, col, value)
            except PermissionError:
                continue

            yield StepEvent(
                step_type="assign",
                cell=(row, col),
                value=value,
                candidates=candidates,
                reason="Tentando candidato (backtracking simples)",
                board=new_board,
                depth=depth,
            )

            result = yield from self._search_events(new_board, depth + 1)
            if isinstance(result, Board):
                return result

            self._metrics.backtracks += 1
            yield StepEvent(
                step_type="backtrack",
                cell=(row, col),
                value=0,
                candidates=candidates,
                reason="Retornando após falha",
                board=board,
                depth=depth,
            )

        return None

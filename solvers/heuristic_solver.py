"""Solver de backtracking com heurísticas (MRV/LCV) e modo explicação."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Optional

from core.board import Board
from core.rules import SudokuRules

from .base import Solver
from .heuristics import get_candidates, order_candidates_lcv, select_cell_mrv
from .types import StepEvent


@dataclass
class HeuristicMetrics:
    explored_nodes: int = 0
    backtracks: int = 0
    max_depth: int = 0


class HeuristicBacktrackingSolver(Solver):
    """Backtracking com MRV/LCV e suporte a gerador de passos."""

    def __init__(self, rules: Optional[SudokuRules] = None) -> None:
        self._rules = rules or SudokuRules()
        self._metrics = HeuristicMetrics()

    def metrics(self) -> HeuristicMetrics:
        return self._metrics

    def solve(self, board: Board) -> Optional[Board]:
        """Consome o gerador até o final para compatibilidade com `Solver`."""
        solved_board: Optional[Board] = None
        for event in self.solve_generator(board):
            if event.step_type == "finished" and event.board is not None:
                solved_board = event.board
        return solved_board

    def solve_generator(self, board: Board) -> Iterator[StepEvent]:
        """Gera eventos de explicação passo a passo."""
        self._metrics = HeuristicMetrics()
        yield from self._search(board, depth=0)

    def _search(self, board: Board, depth: int) -> Iterator[StepEvent]:
        self._metrics.explored_nodes += 1
        self._metrics.max_depth = max(self._metrics.max_depth, depth)

        cell = select_cell_mrv(board, self._rules)
        if cell is None:
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

        r, c = cell
        candidates = list(get_candidates(board, r, c, self._rules))
        if not candidates:
            self._metrics.backtracks += 1
            yield StepEvent(
                step_type="backtrack",
                cell=cell,
                value=0,
                candidates=[],
                reason="Sem candidatos; retornar",
                board=board,
                depth=depth,
            )
            return None

        ordered = order_candidates_lcv(board, r, c, candidates, self._rules)

        for val in ordered:
            try:
                new_board = board.with_value(r, c, val)
            except PermissionError:
                continue

            yield StepEvent(
                step_type="assign",
                cell=cell,
                value=val,
                candidates=ordered,
                reason="Aplicando candidato (LCV)",
                board=new_board,
                depth=depth,
            )

            result = yield from self._search(new_board, depth + 1)
            if isinstance(result, Board):
                return result

            self._metrics.backtracks += 1
            yield StepEvent(
                step_type="backtrack",
                cell=cell,
                value=0,
                candidates=ordered,
                reason="Backtrack após falha",
                board=board,
                depth=depth,
            )

        return None

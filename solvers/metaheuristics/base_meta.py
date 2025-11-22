"""Abstrações compartilhadas para solvers meta-heurísticos.

Esta camada define contratos e utilitários comuns que permitem implementar
algoritmos como Simulated Annealing ou Algoritmos Genéticos sem duplicar
lógica básica de representação, custo e vizinhança.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import isqrt
from random import Random
from typing import Iterable, List, Optional, Sequence

from core.board import Board
from solvers.base import Solver


@dataclass
class MetaheuristicConfig:
    """Configuração genérica para buscas meta-heurísticas."""

    max_iters: int = 10_000
    seed: Optional[int] = None


@dataclass
class MetaheuristicResult:
    """Relatório padronizado das execuções meta-heurísticas."""

    best_board: Board
    best_cost: int
    success: bool
    iterations: int
    cost_history: List[int]


class BaseMetaheuristicSolver(Solver):
    """Base comum para solvers meta-heurísticos.

    Mantém a interface ``Solver`` (``solve`` devolvendo um ``Board`` ou ``None``)
    para integrabilidade com UI e registro, mas expõe também ``solve_with_report``
    para consumidores que precisam dos detalhes (histórico de custo, iterações
    realizadas e melhor tabuleiro).
    """

    name: str = "metaheuristic"

    def __init__(self, config: Optional[MetaheuristicConfig] = None) -> None:
        self.config = config or MetaheuristicConfig()
        self._last_result: Optional[MetaheuristicResult] = None

    def solve(self, board: Board) -> Optional[Board]:  # type: ignore[override]
        """Executa o solver e retorna apenas a solução final."""

        self._last_result = self.solve_with_report(board)
        if self._last_result.success:
            return self._last_result.best_board
        return None

    def solve_with_report(self, board: Board) -> MetaheuristicResult:
        """Executa o solver retornando o relatório completo."""

        self._last_result = self._solve_meta(board)
        return self._last_result

    def last_result(self) -> Optional[MetaheuristicResult]:
        """Retorna o último resultado calculado (se houver)."""

        return self._last_result

    def _rng(self) -> Random:
        """Inicializa um RNG determinístico baseado em ``seed``."""

        return Random(self.config.seed)

    def _fixed_mask(self, board: Board) -> list[list[bool]]:
        """Cria máscara booleana indicando as pistas originais."""

        size = board.size()
        return [[board.is_given(r, c) for c in range(size)] for r in range(size)]

    def _initialize_candidate(self, board: Board, rng: Random) -> Board:
        """Gera um tabuleiro preenchido por linha respeitando as pistas.

        Estratégia didática: para cada linha, coletar os dígitos que faltam
        (1..N) e distribuí-los aleatoriamente nas posições livres. Garante que
        todas as linhas comecem válidas, deixando colunas e subgrades como fonte
        de penalidade da função de custo.
        """

        candidate = board.clone()
        size = candidate.size()
        digits = list(range(1, size + 1))
        for row in range(size):
            current_values = [candidate.get(row, c) for c in range(size)]
            missing = [d for d in digits if d not in current_values]
            free_cols = [c for c in range(size) if not candidate.is_given(row, c)]
            rng.shuffle(missing)
            for col, value in zip(free_cols, missing):
                candidate.set(row, col, value)
        return candidate

    def _random_row_neighbor(
        self, board: Board, fixed_mask: Sequence[Sequence[bool]], rng: Random
    ) -> Board:
        """Gera um vizinho trocando duas células não fixas na mesma linha."""

        size = board.size()
        candidate = board.clone()
        eligible_rows = [
            row
            for row in range(size)
            if sum(1 for col in range(size) if not fixed_mask[row][col]) >= 2
        ]
        if not eligible_rows:
            return candidate

        row_choice = rng.choice(eligible_rows)
        free_cols = [c for c in range(size) if not fixed_mask[row_choice][c]]
        col_a, col_b = rng.sample(free_cols, 2)
        value_a = candidate.get(row_choice, col_a)
        value_b = candidate.get(row_choice, col_b)
        candidate.set(row_choice, col_a, value_b)
        candidate.set(row_choice, col_b, value_a)
        return candidate

    def _sudoku_cost(self, board: Board) -> int:
        """Função de custo clássica: penaliza duplicatas em colunas e blocos."""

        size = board.size()
        block = isqrt(size)
        penalty = 0

        for col in range(size):
            col_values = [board.get(row, col) for row in range(size)]
            penalty += size - len(set(col_values))

        for base_row in range(0, size, block):
            for base_col in range(0, size, block):
                block_values = [
                    board.get(r, c)
                    for r in range(base_row, base_row + block)
                    for c in range(base_col, base_col + block)
                ]
                penalty += size - len(set(block_values))

        return penalty

    def _solve_meta(self, board: Board) -> MetaheuristicResult:
        """Implementação específica de cada meta-heurística."""

        raise NotImplementedError


def cost_history_tail(costs: Iterable[int], limit: int = 20) -> list[int]:
    """Recorta a cauda de um iterável de custos para debug/UI."""

    return list(costs)[-limit:]

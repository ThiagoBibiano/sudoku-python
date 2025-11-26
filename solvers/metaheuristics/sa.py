"""Simulated Annealing para Sudoku."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from core.board import Board
from .base_meta import BaseMetaheuristicSolver, MetaheuristicConfig, MetaheuristicResult


@dataclass
class SimulatedAnnealingConfig(MetaheuristicConfig):
    """Hiperparâmetros específicos do SA."""

    initial_temperature: float = 2.0
    cooling_rate: float = 0.995
    min_temperature: float = 0.01


class SimulatedAnnealingSolver(BaseMetaheuristicSolver):
    """Busca por Simulated Annealing com vizinhança por troca na linha."""

    name: str = "simulated_annealing"

    def __init__(self, config: Optional[SimulatedAnnealingConfig] = None) -> None:
        super().__init__(config or SimulatedAnnealingConfig())

    def _solve_meta(self, board: Board) -> MetaheuristicResult:
        rng = self._rng()
        fixed_mask = self._fixed_mask(board)
        current = self._initialize_candidate(board, rng)
        current_cost = self._sudoku_cost(current)
        best_board = current
        best_cost = current_cost

        temperature = self.config.initial_temperature  # type: ignore[attr-defined]
        cost_history = [current_cost]
        iterations = 0

        for iteration in range(1, self.config.max_iters + 1):
            iterations = iteration
            if best_cost == 0:
                break

            neighbor = self._random_row_neighbor(current, fixed_mask, rng)
            neighbor_cost = self._sudoku_cost(neighbor)
            delta = neighbor_cost - current_cost

            accept = delta <= 0
            if not accept:
                probability = math.exp(-delta / max(temperature, 1e-9))
                accept = rng.random() < probability

            if accept:
                current = neighbor
                current_cost = neighbor_cost
                if current_cost < best_cost:
                    best_board = current
                    best_cost = current_cost

            temperature = max(
                self.config.min_temperature,  # type: ignore[attr-defined]
                temperature * self.config.cooling_rate,  # type: ignore[attr-defined]
            )
            cost_history.append(current_cost)

        success = best_cost == 0
        return MetaheuristicResult(
            best_board=best_board,
            best_cost=best_cost,
            success=success,
            iterations=iterations,
            cost_history=cost_history,
        )

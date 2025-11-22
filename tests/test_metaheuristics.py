"""Testes básicos para a infraestrutura de meta-heurísticas."""
from __future__ import annotations

from solvers.metaheuristics import (
    BaseMetaheuristicSolver,
    MetaheuristicConfig,
    GeneticAlgorithmConfig,
    GeneticAlgorithmSolver,
    SimulatedAnnealingSolver,
)
from solvers.metaheuristics.base_meta import MetaheuristicResult
from solvers.metaheuristics.sa import SimulatedAnnealingConfig
from core.board import Board


class DummyMetaSolver(BaseMetaheuristicSolver):
    """Solver mínimo que usa a própria função de custo."""

    def _solve_meta(self, board: Board) -> MetaheuristicResult:  # type: ignore[override]
        rng = self._rng()
        candidate = self._initialize_candidate(board, rng)
        cost = self._sudoku_cost(candidate)
        return MetaheuristicResult(
            best_board=candidate,
            best_cost=cost,
            success=cost == 0,
            iterations=0,
            cost_history=[cost],
        )


def test_initialize_respects_givens():
    grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    board = Board(grid)
    solver = DummyMetaSolver(MetaheuristicConfig(seed=42))
    candidate = solver._initialize_candidate(board, solver._rng())

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                assert candidate.get(r, c) == value


def test_cost_zero_for_valid_solution():
    solved_grid = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]
    board = Board(solved_grid)
    solver = DummyMetaSolver()
    assert solver._sudoku_cost(board) == 0


def test_simulated_annealing_reports_result():
    solved_grid = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]
    board = Board(solved_grid)
    config = SimulatedAnnealingConfig(max_iters=10, seed=123)
    solver = SimulatedAnnealingSolver(config)

    solution = solver.solve(board)
    result = solver.last_result()

    assert solution is not None
    assert result is not None
    assert result.success
    assert result.best_cost == 0
    assert result.cost_history[0] == 0


def test_genetic_algorithm_reports_result():
    solved_grid = [
        [5, 3, 4, 6, 7, 8, 9, 1, 2],
        [6, 7, 2, 1, 9, 5, 3, 4, 8],
        [1, 9, 8, 3, 4, 2, 5, 6, 7],
        [8, 5, 9, 7, 6, 1, 4, 2, 3],
        [4, 2, 6, 8, 5, 3, 7, 9, 1],
        [7, 1, 3, 9, 2, 4, 8, 5, 6],
        [9, 6, 1, 5, 3, 7, 2, 8, 4],
        [2, 8, 7, 4, 1, 9, 6, 3, 5],
        [3, 4, 5, 2, 8, 6, 1, 7, 9],
    ]
    board = Board(solved_grid)
    config = GeneticAlgorithmConfig(
        pop_size=8,
        n_generations=5,
        mutation_rate=0.3,
        crossover_rate=0.9,
        tournament_size=2,
        seed=321,
    )
    solver = GeneticAlgorithmSolver(config)

    solution = solver.solve(board)
    result = solver.last_result()

    assert solution is not None
    assert result is not None
    assert result.success
    assert result.best_cost == 0
    assert result.cost_history[0] == 0

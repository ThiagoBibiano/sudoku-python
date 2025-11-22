"""Algoritmo Genético simples para Sudoku."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from core.board import Board
from .base_meta import BaseMetaheuristicSolver, MetaheuristicConfig, MetaheuristicResult


@dataclass
class GeneticAlgorithmConfig(MetaheuristicConfig):
    """Hiperparâmetros do Algoritmo Genético."""

    pop_size: int = 50
    n_generations: int = 200
    crossover_rate: float = 0.8
    mutation_rate: float = 0.2
    tournament_size: int = 3
    elite_fraction: float = 0.1


class GeneticAlgorithmSolver(BaseMetaheuristicSolver):
    """Algoritmo Genético com crossover por linha e mutação de vizinho."""

    name: str = "genetic_algorithm"

    def __init__(self, config: Optional[GeneticAlgorithmConfig] = None) -> None:
        super().__init__(config or GeneticAlgorithmConfig())

    def _solve_meta(self, board: Board) -> MetaheuristicResult:
        rng = self._rng()
        fixed_mask = self._fixed_mask(board)
        pop_size = max(2, self.config.pop_size)  # type: ignore[attr-defined]
        generations = max(1, self.config.n_generations)  # type: ignore[attr-defined]

        population = [self._initialize_candidate(board, rng) for _ in range(pop_size)]
        costs = [self._sudoku_cost(individual) for individual in population]

        best_idx = int(min(range(pop_size), key=lambda i: costs[i]))
        best_board = population[best_idx]
        best_cost = costs[best_idx]
        success = best_cost == 0
        cost_history = [best_cost]

        for iteration in range(1, generations + 1):
            if best_cost == 0:
                break

            elite_count = max(1, int(pop_size * self.config.elite_fraction))  # type: ignore[attr-defined]
            ranked = sorted(zip(costs, population), key=lambda pair: pair[0])
            elites = [board.clone() for _, board in ranked[:elite_count]]

            new_population = elites.copy()
            while len(new_population) < pop_size:
                parent_a = self._tournament_select(population, costs, rng)
                parent_b = self._tournament_select(population, costs, rng)

                if rng.random() < self.config.crossover_rate:  # type: ignore[attr-defined]
                    child = self._crossover_by_row(parent_a, parent_b, fixed_mask, rng)
                else:
                    child = parent_a.clone()

                if rng.random() < self.config.mutation_rate:  # type: ignore[attr-defined]
                    child = self._random_row_neighbor(child, fixed_mask, rng)

                new_population.append(child)

            population = new_population
            costs = [self._sudoku_cost(individual) for individual in population]

            generation_best_idx = int(min(range(pop_size), key=lambda i: costs[i]))
            generation_best_cost = costs[generation_best_idx]
            if generation_best_cost < best_cost:
                best_cost = generation_best_cost
                best_board = population[generation_best_idx]
                success = best_cost == 0

            cost_history.append(best_cost)

        return MetaheuristicResult(
            best_board=best_board,
            best_cost=best_cost,
            success=success,
            iterations=iteration,
            cost_history=cost_history,
        )

    def _tournament_select(
        self,
        population: Sequence[Board],
        costs: Sequence[int],
        rng,
    ) -> Board:
        size = min(len(population), max(1, self.config.tournament_size))  # type: ignore[attr-defined]
        contenders = rng.sample(range(len(population)), k=size)
        best_idx = min(contenders, key=lambda idx: costs[idx])
        return population[best_idx]

    def _crossover_by_row(
        self,
        parent_a: Board,
        parent_b: Board,
        fixed_mask: Sequence[Sequence[bool]],
        rng,
    ) -> Board:
        size = parent_a.size()
        child = parent_a.clone()

        for row in range(size):
            source = parent_a if rng.random() < 0.5 else parent_b
            for col in range(size):
                if not fixed_mask[row][col]:
                    child.set(row, col, source.get(row, col))
        return child

"""Infra de meta-heurísticas para Sudoku."""
from __future__ import annotations

from .base_meta import (
    BaseMetaheuristicSolver,
    MetaheuristicConfig,
    MetaheuristicResult,
    cost_history_tail,
)
from .ga import GeneticAlgorithmConfig, GeneticAlgorithmSolver
from .sa import SimulatedAnnealingConfig, SimulatedAnnealingSolver

__all__ = [
    "BaseMetaheuristicSolver",
    "MetaheuristicConfig",
    "MetaheuristicResult",
    "GeneticAlgorithmConfig",
    "GeneticAlgorithmSolver",
    "SimulatedAnnealingConfig",
    "SimulatedAnnealingSolver",
    "cost_history_tail",
]

"""Exporta solvers e facilita o registro automático."""
from __future__ import annotations

from .backtracking import BacktrackingSolver
from .heuristic_solver import HeuristicBacktrackingSolver
from .registry import register

register("backtracking", BacktrackingSolver)
register("heuristic_backtracking", HeuristicBacktrackingSolver)

__all__ = ["BacktrackingSolver", "HeuristicBacktrackingSolver"]

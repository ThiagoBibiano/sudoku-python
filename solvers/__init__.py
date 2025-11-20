"""Exporta solvers e facilita o registro automático."""
from __future__ import annotations

from .backtracking import BacktrackingSolver
from .heuristic_solver import HeuristicBacktrackingSolver
from .forward_checking import ForwardCheckingSolver
from .registry import register

register("backtracking", BacktrackingSolver)
register("heuristic_backtracking", HeuristicBacktrackingSolver)
register("forward_checking", ForwardCheckingSolver)

__all__ = ["BacktrackingSolver", "HeuristicBacktrackingSolver", "ForwardCheckingSolver"]

"""Exporta solvers e facilita o registro automático."""
from __future__ import annotations

from .backtracking import BacktrackingSolver
from .registry import register

register("backtracking", BacktrackingSolver)

__all__ = ["BacktrackingSolver"]

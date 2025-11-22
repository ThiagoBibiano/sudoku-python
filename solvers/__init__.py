"""Exporta solvers e facilita o registro automático."""
from __future__ import annotations

from .backtracking import BacktrackingSolver
from .heuristic_solver import HeuristicBacktrackingSolver
from .forward_checking import ForwardCheckingSolver
from .heuristic_solver import HeuristicBacktrackingSolver
from .metaheuristics import SimulatedAnnealingSolver
try:
    from .cp_sat import CpSatSolver
except ImportError:  # ortools pode não estar instalado
    CpSatSolver = None  # type: ignore[assignment]
from .dlx_solver import DlxSolver
from .registry import register

register("backtracking", BacktrackingSolver)
register("heuristic_backtracking", HeuristicBacktrackingSolver)
register("forward_checking", ForwardCheckingSolver)
register("simulated_annealing", SimulatedAnnealingSolver)
if CpSatSolver is not None:
    register("cp_sat", CpSatSolver)
register("dlx", DlxSolver)

__all__ = ["BacktrackingSolver", "HeuristicBacktrackingSolver", "ForwardCheckingSolver", "CpSatSolver", "DlxSolver"]
__all__ = [
    "BacktrackingSolver",
    "HeuristicBacktrackingSolver",
    "ForwardCheckingSolver",
    "SimulatedAnnealingSolver",
    "CpSatSolver",
    "DlxSolver",
]

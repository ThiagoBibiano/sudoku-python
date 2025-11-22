"""Testes para o solver CP-SAT (Google OR-Tools)."""
from __future__ import annotations

from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from solvers import CpSatSolver
    from core.board import Board
    from core.rules import SudokuRules
except ImportError as exc:  # ortools ausente
    CpSatSolver = None  # type: ignore
    pytest.skip(f"OR-Tools não instalado: {exc}", allow_module_level=True)


EASY_PUZZLE = [
    [0, 0, 0, 2, 6, 0, 7, 0, 1],
    [6, 8, 0, 0, 7, 0, 0, 9, 0],
    [1, 9, 0, 0, 0, 4, 5, 0, 0],
    [8, 2, 0, 1, 0, 0, 0, 4, 0],
    [0, 0, 4, 6, 0, 2, 9, 0, 0],
    [0, 5, 0, 0, 0, 3, 0, 2, 8],
    [0, 0, 9, 3, 0, 0, 0, 7, 4],
    [0, 4, 0, 0, 5, 0, 0, 3, 6],
    [7, 0, 3, 0, 1, 8, 0, 0, 0],
]


@pytest.mark.skipif(CpSatSolver is None, reason="OR-Tools não instalado")
def test_cp_sat_solves_puzzle() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = CpSatSolver()
    solved = solver.solve(board)

    assert solved is not None
    assert SudokuRules().is_solved(solved)

    metrics = solver.metrics()
    assert metrics is not None
    assert metrics.status in {"OPTIMAL", "FEASIBLE"}
    assert metrics.branches >= 0

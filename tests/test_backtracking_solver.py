"""Testes para o solver básico de backtracking."""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.board import Board
from core.rules import SudokuRules
from solvers import BacktrackingSolver
from solvers.types import StepEvent
from solvers.registry import all_registered, get


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


def test_backtracking_solver_solves_puzzle() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = BacktrackingSolver()
    solved = solver.solve(board)

    assert solved is not None
    assert SudokuRules().is_solved(solved)
    assert board.get(0, 0) == 0


def test_solver_registry_exposes_backtracking_solver() -> None:
    registry_snapshot = all_registered()
    assert "backtracking" in registry_snapshot
    assert get("backtracking") is BacktrackingSolver


def test_backtracking_solver_generator_emits_events() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = BacktrackingSolver()
    events = list(solver.solve_generator(board))

    assert any(isinstance(ev, StepEvent) and ev.step_type == "assign" for ev in events)
    assert any(ev.step_type == "finished" for ev in events)

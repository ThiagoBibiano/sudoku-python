"""Testes para o solver heurístico com MRV/LCV e modo generator."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.board import Board
from core.rules import SudokuRules
from solvers import HeuristicBacktrackingSolver
from solvers.types import StepEvent


EASY_PUZZLE: List[List[int]] = [
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


def test_heuristic_solver_solves_puzzle() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = HeuristicBacktrackingSolver()
    solved = solver.solve(board)

    assert solved is not None
    assert SudokuRules().is_solved(solved)
    assert board.get(0, 0) == 0


def test_heuristic_solver_generator_emits_events() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = HeuristicBacktrackingSolver()
    events = list(solver.solve_generator(board))

    assert any(isinstance(ev, StepEvent) and ev.step_type == "assign" for ev in events)
    assert any(ev.step_type == "finished" for ev in events)

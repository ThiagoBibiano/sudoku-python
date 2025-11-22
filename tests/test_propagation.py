"""Testes para o solver de Forward Checking (propagação de domínios)."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.board import Board
from core.rules import SudokuRules
from solvers import BacktrackingSolver, ForwardCheckingSolver


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


def test_forward_checking_solves_puzzle() -> None:
    board = Board(EASY_PUZZLE, n=3)
    solver = ForwardCheckingSolver()
    solved = solver.solve(board)

    assert solved is not None
    assert SudokuRules().is_solved(solved)


def test_forward_checking_explores_no_more_than_backtracking() -> None:
    board = Board(EASY_PUZZLE, n=3)

    brute = BacktrackingSolver()
    brute.solve(board)
    brute_nodes = brute.metrics().explored_nodes

    fc = ForwardCheckingSolver()
    fc.solve(board)
    fc_nodes = fc.metrics().explored_nodes

    assert fc_nodes <= brute_nodes

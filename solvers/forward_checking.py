"""Solver com Forward Checking e domínios (propagação de candidatos)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from core.board import Board
from core.state import State
from core.rules import SudokuRules

from .base import Solver


@dataclass
class ForwardMetrics:
    explored_nodes: int = 0
    backtracks: int = 0
    max_depth: int = 0


class ForwardCheckingSolver(Solver):
    """Backtracking com propagação de domínios (forward checking)."""

    def __init__(self, rules: Optional[SudokuRules] = None) -> None:
        self._rules = rules or SudokuRules()
        self._metrics = ForwardMetrics()

    def metrics(self) -> ForwardMetrics:
        return self._metrics

    def solve(self, board: Board) -> Optional[Board]:
        self._metrics = ForwardMetrics()
        state = State(board)
        return self._search(state, depth=0)

    def _search(self, state: State, depth: int) -> Optional[Board]:
        self._metrics.explored_nodes += 1
        self._metrics.max_depth = max(self._metrics.max_depth, depth)

        if state.board.is_full():
            return state.board if self._rules.is_solved(state.board) else None

        cell = self._select_cell(state)
        if cell is None:
            return None

        r, c = cell
        candidates = list(sorted(state.domains[(r, c)]))
        for val in candidates:
            new_state = state.clone()
            ok = new_state.assign(r, c, val)
            if not ok:
                self._metrics.backtracks += 1
                continue

            solved = self._search(new_state, depth + 1)
            if solved is not None:
                return solved

            self._metrics.backtracks += 1

        return None

    def _select_cell(self, state: State) -> Optional[Tuple[int, int]]:
        """Escolhe célula vazia usando MRV com domínios atuais."""
        size = state.board.size()
        best = None
        best_len = None
        for r in range(size):
            for c in range(size):
                if state.board.get(r, c) != 0:
                    continue
                domain_size = len(state.domains[(r, c)])
                if best_len is None or domain_size < best_len:
                    best = (r, c)
                    best_len = domain_size
                    if best_len == 1:
                        return best
        return best

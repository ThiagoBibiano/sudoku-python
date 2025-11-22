"""Solver de Sudoku usando CP-SAT (Google OR-Tools)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ortools.sat.python import cp_model

from core.board import Board
from core.rules import SudokuRules
from core.types import EMPTY
from .base import Solver


STATUS_NAMES = {
    cp_model.OPTIMAL: "OPTIMAL",
    cp_model.FEASIBLE: "FEASIBLE",
    cp_model.INFEASIBLE: "INFEASIBLE",
    cp_model.UNKNOWN: "UNKNOWN",
    cp_model.MODEL_INVALID: "MODEL_INVALID",
}


@dataclass
class CpSatMetrics:
    status: str
    wall_time_ms: float
    branches: int
    conflicts: int

    @property
    def explored_nodes(self) -> int:
        # Proxy: OR-Tools expõe ramificações como melhor aproximação de "nós"
        return self.branches


class CpSatSolver(Solver):
    """Tradução declarativa das regras de Sudoku para CP-SAT."""

    def __init__(self, rules: Optional[SudokuRules] = None) -> None:
        self._rules = rules or SudokuRules()
        self._metrics: Optional[CpSatMetrics] = None

    def solve(self, board: Board) -> Optional[Board]:
        size = board.size()
        n = int(size ** 0.5)

        model = cp_model.CpModel()

        grid_vars = [
            [model.NewIntVar(1, size, f"cell_{r}_{c}") for c in range(size)]
            for r in range(size)
        ]

        # Células pré-preenchidas
        for r in range(size):
            for c in range(size):
                v = board.get(r, c)
                if v != EMPTY:
                    model.Add(grid_vars[r][c] == v)

        # Restrições de linhas
        for r in range(size):
            model.AddAllDifferent(grid_vars[r])

        # Restrições de colunas
        for c in range(size):
            model.AddAllDifferent([grid_vars[r][c] for r in range(size)])

        # Restrições de caixas
        for br in range(0, size, n):
            for bc in range(0, size, n):
                box = [
                    grid_vars[r][c]
                    for r in range(br, br + n)
                    for c in range(bc, bc + n)
                ]
                model.AddAllDifferent(box)

        solver = cp_model.CpSolver()
        status = solver.Solve(model)

        self._metrics = CpSatMetrics(
            status=STATUS_NAMES.get(status, str(status)),
            wall_time_ms=solver.WallTime() * 1000.0,
            branches=solver.NumBranches(),
            conflicts=solver.NumConflicts(),
        )

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            return None

        solved_grid = [
            [int(solver.Value(grid_vars[r][c])) for c in range(size)]
            for r in range(size)
        ]

        solved_board = Board(solved_grid, n=n)
        return solved_board if self._rules.is_solved(solved_board) else None

    def metrics(self) -> Optional[CpSatMetrics]:
        return self._metrics

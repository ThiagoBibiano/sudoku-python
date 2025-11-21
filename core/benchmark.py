"""Motor de benchmark para comparar solvers em lote."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import pandas as pd

from core.io import PuzzleEntry
from core.rules import SudokuRules
from solvers.registry import get


@dataclass
class BenchmarkResult:
    puzzle_id: str
    solver_name: str
    duration_sec: float
    explored_nodes: Optional[int]
    status: str


class BenchmarkSession:
    """Executa benchmarks sobre uma lista de puzzles e solvers registrados."""

    def __init__(self, *, timeout: float = 10.0) -> None:
        self.timeout = timeout
        self._rules = SudokuRules()

    def run(self, solvers: List[str], puzzles: Iterable[PuzzleEntry]) -> pd.DataFrame:
        results: List[BenchmarkResult] = []

        for solver_name in solvers:
            solver_cls = get(solver_name)
            for entry in puzzles:
                board = entry.board.clone()
                solver = solver_cls()
                start = time.perf_counter()
                status = "ok"
                explored_nodes: Optional[int] = None

                try:
                    solved = self._run_with_timeout(solver, board, self.timeout)
                    duration = time.perf_counter() - start
                    if solved is None or not self._rules.is_solved(solved):
                        status = "fail"
                    explored_nodes = self._extract_nodes(solver)
                except TimeoutError:
                    duration = self.timeout
                    status = "timeout"
                except Exception:
                    duration = time.perf_counter() - start
                    status = "error"

                results.append(
                    BenchmarkResult(
                        puzzle_id=entry.id,
                        solver_name=solver_name,
                        duration_sec=duration,
                        explored_nodes=explored_nodes,
                        status=status,
                    )
                )

        df = pd.DataFrame(
            [
                {
                    "Puzzle ID": r.puzzle_id,
                    "Solver": r.solver_name,
                    "Time (s)": r.duration_sec,
                    "Nodes": r.explored_nodes,
                    "Status": r.status,
                }
                for r in results
            ]
        )
        return df

    def _run_with_timeout(self, solver, board, timeout: float):
        start = time.perf_counter()
        result = solver.solve(board)
        elapsed = time.perf_counter() - start
        if elapsed > timeout:
            raise TimeoutError("Solver exceeded timeout.")
        return result

    def _extract_nodes(self, solver) -> Optional[int]:
        """Tenta extrair 'explored_nodes' das métricas, se houver."""
        metrics_fn = getattr(solver, "metrics", None)
        if not callable(metrics_fn):
            return None
        metrics = metrics_fn()
        return getattr(metrics, "explored_nodes", None)

"""Solver de Sudoku via Dancing Links (Algorithm X / DLX)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.board import Board
from core.rules import SudokuRules
from core.types import EMPTY
from .base import Solver
from .dlx_lib import ColumnHeader, DataObject, cover, search, uncover


@dataclass
class DlxMetrics:
    solutions: int = 0
    explored_rows: int = 0

    @property
    def explored_nodes(self) -> int:
        # usa linhas visitadas como aproximação de nós
        return self.explored_rows


class DlxSolver(Solver):
    """Transforma Sudoku em Exact Cover e resolve com DLX."""

    def __init__(self, rules: Optional[SudokuRules] = None) -> None:
        self._rules = rules or SudokuRules()
        self._metrics = DlxMetrics()

    def metrics(self) -> DlxMetrics:
        return self._metrics

    def solve(self, board: Board) -> Optional[Board]:
        self._metrics = DlxMetrics()
        size = board.size()
        n = int(size ** 0.5)

        root, columns = self._build_headers(size)
        rows_map: List[Tuple[int, int, int]] = []

        # constrói linhas de possibilidades (r, c, v)
        for r in range(size):
            for c in range(size):
                if board.get(r, c) != EMPTY:
                    # Apenas o valor já definido
                    v = board.get(r, c)
                    if self._rules.can_place(board, r, c, v):
                        self._append_option(root, columns, rows_map, r, c, v, size, n)
                    continue
                for v in range(1, size + 1):
                    if self._rules.can_place(board, r, c, v):
                        self._append_option(root, columns, rows_map, r, c, v, size, n)

        solution_nodes: Optional[List[DataObject]] = None
        for sol in search(root, []):
            solution_nodes = sol
            self._metrics.solutions += 1
            break  # pegamos apenas a primeira solução

        if solution_nodes is None:
            return None

        solved_grid = [[board.get(r, c) for c in range(size)] for r in range(size)]
        for node in solution_nodes:
            r, c, v = rows_map[node_to_index(node)]
            solved_grid[r][c] = v

        self._metrics.explored_rows = len(rows_map)

        solved_board = Board(solved_grid, n=n)
        return solved_board if self._rules.is_solved(solved_board) else None

    def _build_headers(self, size: int) -> Tuple[ColumnHeader, List[ColumnHeader]]:
        total_cols = 4 * size * size
        root = ColumnHeader("root")
        columns: List[ColumnHeader] = []

        last = root
        for i in range(total_cols):
            col = ColumnHeader(str(i))
            columns.append(col)
            # insere à direita
            col.left = last
            col.right = root
            last.right = col
            root.left = col
            last = col
        return root, columns

    def _append_option(
        self,
        root: ColumnHeader,
        columns: List[ColumnHeader],
        rows_map: List[Tuple[int, int, int]],
        r: int,
        c: int,
        v: int,
        size: int,
        n: int,
    ) -> None:
        """Cria nós de uma linha (r, c, v) e conecta colunas correspondentes."""
        cell_col = r * size + c
        row_col = size * size + r * size + (v - 1)
        col_col = 2 * size * size + c * size + (v - 1)
        box_idx = (r // n) * n + (c // n)
        box_col = 3 * size * size + box_idx * size + (v - 1)

        col_indices = [cell_col, row_col, col_col, box_col]
        nodes = [DataObject(columns[idx]) for idx in col_indices]
        rows_map.append((r, c, v))
        row_id = len(rows_map) - 1

        # conecta verticalmente
        for node, col_idx in zip(nodes, col_indices):
            col = columns[col_idx]
            node.down = col
            node.up = col.up
            col.up.down = node
            col.up = node
            col.size += 1

        # conecta horizontalmente em ciclo
        for i in range(4):
            nodes[i].right = nodes[(i + 1) % 4]
            nodes[i].left = nodes[(i - 1) % 4]

        # armazena índice da linha no próprio node (via atributo dinâmico)
        for node in nodes:
            node.row_id = row_id  # type: ignore[attr-defined]


def node_to_index(node: DataObject) -> int:
    """Recupera o índice da linha armazenado no node (helper)."""
    return getattr(node, "row_id")

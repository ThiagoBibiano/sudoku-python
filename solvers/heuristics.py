"""Heurísticas de apoio para solvers de Sudoku (MRV e LCV)."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Set, Tuple

from core.board import Board
from core.rules import SudokuRules


def get_candidates(board: Board, r: int, c: int, rules: SudokuRules) -> Set[int]:
    """Retorna o conjunto de candidatos válidos para (r, c)."""
    size = board.size()
    return {v for v in range(1, size + 1) if rules.can_place(board, r, c, v)}


def select_cell_mrv(board: Board, rules: SudokuRules) -> Tuple[int, int] | None:
    """Seleciona a próxima célula usando MRV (Minimum Remaining Values)."""
    size = board.size()
    best_cell = None
    best_count = None

    for r in range(size):
        for c in range(size):
            if board.get(r, c) != 0:
                continue
            candidates = get_candidates(board, r, c, rules)
            count = len(candidates)
            if count == 0:
                return (r, c)  # dead end explícito
            if best_count is None or count < best_count:
                best_cell = (r, c)
                best_count = count
                if best_count == 1:
                    return best_cell  # menor valor possível

    return best_cell


def order_candidates_lcv(
    board: Board,
    r: int,
    c: int,
    candidates: Iterable[int],
    rules: SudokuRules,
) -> List[int]:
    """Ordena candidatos usando LCV (Least Constraining Value)."""
    scored: List[tuple[int, int]] = []

    neighbors = _collect_neighbors(board, r, c)
    for val in candidates:
        impact = 0
        for nr, nc in neighbors:
            if board.get(nr, nc) != 0:
                continue
            try:
                if rules.can_place(board, nr, nc, val):
                    impact += 1
            except Exception:
                continue
        scored.append((impact, val))

    scored.sort(key=lambda t: (t[0], t[1]))
    return [val for _, val in scored]


def _collect_neighbors(board: Board, r: int, c: int) -> List[Tuple[int, int]]:
    """Retorna células na mesma linha/coluna/caixa (sem duplicar)."""
    size = board.size()
    n = int(size ** 0.5)
    coords = set()

    # linha e coluna
    for i in range(size):
        if i != c:
            coords.add((r, i))
        if i != r:
            coords.add((i, c))

    # caixa
    br = (r // n) * n
    bc = (c // n) * n
    for rr in range(br, br + n):
        for cc in range(bc, bc + n):
            if rr == r and cc == c:
                continue
            coords.add((rr, cc))

    return list(coords)

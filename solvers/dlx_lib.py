"""Implementação mínima de Dancing Links (DLX) para Exact Cover."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator, List, Optional


class DataObject:
    """Nó da matriz dançante."""

    def __init__(self, column: Optional["ColumnHeader"] = None) -> None:
        self.left: DataObject = self
        self.right: DataObject = self
        self.up: DataObject = self
        self.down: DataObject = self
        self.column: Optional["ColumnHeader"] = column


class ColumnHeader(DataObject):
    """Cabeçalho de coluna com contagem de nós."""

    def __init__(self, name: str) -> None:
        super().__init__(self)
        self.size: int = 0
        self.name: str = name


def cover(column: ColumnHeader) -> None:
    """Remove uma coluna e suas linhas associadas."""
    column.right.left = column.left
    column.left.right = column.right

    i = column.down
    while i is not column:
        j = i.right
        while j is not i:
            j.down.up = j.up
            j.up.down = j.down
            if j.column:
                j.column.size -= 1
            j = j.right
        i = i.down


def uncover(column: ColumnHeader) -> None:
    """Reverte a operação de cover, restaurando nós."""
    i = column.up
    while i is not column:
        j = i.left
        while j is not i:
            if j.column:
                j.column.size += 1
            j.down.up = j
            j.up.down = j
            j = j.left
        i = i.up
    column.right.left = column
    column.left.right = column


def search(root: ColumnHeader, solution: List[DataObject]) -> Generator[List[DataObject], None, None]:
    """Algorithm X de Knuth usando DLX. Gera soluções."""
    if root.right is root:
        yield list(solution)
        return

    # Heurística: coluna com menor size
    c = _choose_column(root)
    if c is None:
        return
    cover(c)

    r = c.down
    while r is not c:
        solution.append(r)
        j = r.right
        while j is not r:
            if j.column:
                cover(j.column)
            j = j.right

        yield from search(root, solution)

        # backtrack
        solution.pop()
        j = r.left
        while j is not r:
            if j.column:
                uncover(j.column)
            j = j.left

        r = r.down

    uncover(c)


def _choose_column(root: ColumnHeader) -> Optional[ColumnHeader]:
    """Escolhe coluna com menor size (heurística S)."""
    c = root.right
    best: Optional[ColumnHeader] = None
    min_size = float("inf")
    while isinstance(c, ColumnHeader) and c is not root:
        if c.size < min_size:
            min_size = c.size
            best = c
        c = c.right
    return best

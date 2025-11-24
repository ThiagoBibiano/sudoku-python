"""Pipeline de dados para treino supervisionado/RL a partir do CSV gigante.

Projetado para **streaming**: não carrega todo o dataset (9M) em RAM,
usa `IterableDataset` e leitura incremental via `csv`.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import numpy as np

try:
    import torch
    from torch.utils.data import DataLoader, IterableDataset, get_worker_info
except ImportError as exc:  # pragma: no cover - só avaliado quando torch não existe
    torch = None
    DataLoader = None  # type: ignore[assignment]
    IterableDataset = object  # type: ignore[assignment]
    get_worker_info = None  # type: ignore[assignment]
    _TORCH_IMPORT_ERROR = exc

Grid = List[List[int]]
Example = Dict[str, "torch.Tensor"]


def _require_torch() -> None:
    if torch is None:
        raise ImportError(
            "torch é obrigatório para usar o pipeline de dados "
            f"(erro original: {_TORCH_IMPORT_ERROR})"
        )


def puzzle_str_to_grid(puzzle: str, n: int = 3) -> Grid:
    """Converte string (81 chars) em grade 9x9."""
    size = n * n
    expected_len = size * size
    if len(puzzle) != expected_len:
        raise ValueError(f"Puzzle deve ter {expected_len} chars; recebido {len(puzzle)}.")
    digits = [int(ch) for ch in puzzle]
    grid: Grid = []
    for i in range(0, expected_len, size):
        grid.append(digits[i : i + size])
    return grid


def encode_puzzle_one_hot(grid: Grid, include_given_channel: bool = True) -> "torch.Tensor":
    """One-hot (size,size,10) com canal extra para pistas iniciais."""
    _require_torch()
    size = len(grid)
    channels = size + (1 if include_given_channel else 0)
    tensor = torch.zeros((size, size, channels), dtype=torch.float32)
    given_idx = channels - 1 if include_given_channel else None
    for r in range(size):
        for c in range(size):
            v = grid[r][c]
            if v > 0:
                tensor[r, c, v - 1] = 1.0
                if given_idx is not None:
                    tensor[r, c, given_idx] = 1.0
    return tensor


def givens_mask(grid: Grid) -> "torch.Tensor":
    """Máscara booleana indicando pistas iniciais."""
    _require_torch()
    arr = np.array(grid)
    return torch.from_numpy(arr > 0)


class SudokuCSVDataset(IterableDataset):  # type: ignore[misc]
    """Dataset iterável que lê puzzles de um CSV gigantesco (streaming)."""

    def __init__(
        self,
        csv_path: str | Path,
        *,
        n: int = 3,
        max_rows: Optional[int] = None,
        start_row: int = 0,
    ) -> None:
        _require_torch()
        self.csv_path = Path(csv_path)
        self.n = n
        self.size = n * n
        self.max_rows = max_rows
        self.start_row = max(0, int(start_row))
        if not self.csv_path.exists():
            raise FileNotFoundError(f"CSV não encontrado: {self.csv_path}")

    def __iter__(self) -> Iterator[Example]:
        worker = get_worker_info() if get_worker_info else None
        worker_id = worker.id if worker else 0
        num_workers = worker.num_workers if worker else 1
        read_count = 0

        def row_iter() -> Iterator[Tuple[str, str]]:
            nonlocal read_count
            with self.csv_path.open("r", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # header
                for idx, row in enumerate(reader):
                    if idx < self.start_row:
                        continue
                    if self.max_rows is not None and read_count >= self.max_rows:
                        break
                    if (idx - worker_id) % num_workers != 0:
                        continue
                    if len(row) < 2:
                        continue
                    read_count += 1
                    yield row[0], row[1]

        for puzzle_str, solution_str in row_iter():
            puzzle_grid = puzzle_str_to_grid(puzzle_str, self.n)
            solution_grid = puzzle_str_to_grid(solution_str, self.n)
            obs = encode_puzzle_one_hot(puzzle_grid)
            target = torch.tensor(solution_grid, dtype=torch.long)
            given = givens_mask(puzzle_grid)
            yield {"obs": obs, "target": target, "given_mask": given}


def build_dataloader(
    csv_path: str | Path,
    *,
    batch_size: int = 32,
    num_workers: int = 0,
    max_rows: Optional[int] = None,
    start_row: int = 0,
    n: int = 3,
) -> DataLoader:
    """Cria DataLoader com streaming (sem carregar 9M em RAM)."""
    _require_torch()
    dataset = SudokuCSVDataset(csv_path, n=n, max_rows=max_rows, start_row=start_row)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        num_workers=num_workers,
        pin_memory=False,
    )

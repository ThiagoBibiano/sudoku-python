from pathlib import Path
import sys
import tempfile

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import torch
    from solvers.rl.data import (
        SudokuCSVDataset,
        build_dataloader,
        encode_puzzle_one_hot,
        givens_mask,
        puzzle_str_to_grid,
    )
except ImportError:
    torch = None  # type: ignore[assignment]


pytestmark = pytest.mark.skipif(torch is None, reason="torch não instalado")


def _fake_puzzle_pair():
    solution = "123456789" * 9
    puzzle = list(solution)
    puzzle[0] = "0"
    puzzle[10] = "0"
    puzzle_str = "".join(puzzle)
    return puzzle_str, solution


def test_puzzle_str_to_grid_and_encoders():
    puzzle_str, _ = _fake_puzzle_pair()
    grid = puzzle_str_to_grid(puzzle_str)
    assert len(grid) == 9 and len(grid[0]) == 9

    one_hot = encode_puzzle_one_hot(grid)
    assert one_hot.shape == (9, 9, 10)
    assert one_hot[0, 0].sum() == 0  # célula vazia
    assert one_hot[0, 1, 1] == 1  # valor 2 presente

    gm = givens_mask(grid)
    assert gm.shape == (9, 9)
    assert gm[0, 0].item() is False
    assert gm[0, 1].item() is True


def test_csv_dataset_streaming_and_dataloader():
    puzzle_str, solution_str = _fake_puzzle_pair()
    header = "puzzle,solution\n"
    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write(header)
        tmp.write(f"{puzzle_str},{solution_str}\n")
        tmp.write(f"{puzzle_str},{solution_str}\n")
        csv_path = tmp.name

    dataset = SudokuCSVDataset(csv_path, max_rows=1)
    rows = list(dataset)
    assert len(rows) == 1  # max_rows respeitado
    sample = rows[0]
    assert sample["obs"].shape == (9, 9, 10)
    assert sample["target"].shape == (9, 9)
    assert sample["given_mask"].shape == (9, 9)

    loader = build_dataloader(csv_path, batch_size=2, max_rows=2)
    batch = next(iter(loader))
    assert batch["obs"].shape == (2, 9, 9, 10)
    assert batch["target"].shape == (2, 9, 9)
    Path(csv_path).unlink(missing_ok=True)


def test_dataset_respects_start_row():
    # Cria dois registros distintos para verificar o offset
    header = "puzzle,solution\n"
    puzzle_a = "100000000" + "0" * 72  # célula (0,0)=1
    solution_a = "1" * 81
    puzzle_b = "900000000" + "0" * 72  # célula (0,0)=9
    solution_b = "9" * 81

    with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
        tmp.write(header)
        tmp.write(f"{puzzle_a},{solution_a}\n")  # row 0
        tmp.write(f"{puzzle_b},{solution_b}\n")  # row 1
        csv_path = tmp.name

    dataset = SudokuCSVDataset(csv_path, start_row=1, max_rows=1)
    rows = list(dataset)
    assert len(rows) == 1
    # Deve ler apenas o segundo registro (com dígito 9 na primeira célula)
    assert rows[0]["target"][0, 0].item() == 9
    Path(csv_path).unlink(missing_ok=True)

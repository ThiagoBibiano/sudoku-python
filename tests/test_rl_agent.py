from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import torch
    from solvers.rl.agent import SudokuNet
except ImportError:
    torch = None  # type: ignore[assignment]


pytestmark = pytest.mark.skipif(torch is None, reason="torch não instalado")


def test_sudoku_net_preserves_spatial_shape():
    model = SudokuNet(num_blocks=2, hidden_dim=16)
    inp = torch.zeros((4, 9, 9, 10))
    out = model(inp)
    assert out.shape == (4, 9, 9, 9)

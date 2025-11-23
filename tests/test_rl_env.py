from pathlib import Path
import sys

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.board import Board

try:
    from solvers.rl.env import SudokuGymEnv
    import gymnasium as gym
except ImportError:
    gym = None
    SudokuGymEnv = None  # type: ignore[assignment]


pytestmark = pytest.mark.skipif(
    gym is None, reason="gymnasium não está instalado para testar o ambiente RL"
)


def _sample_board() -> Board:
    grid = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9],
    ]
    return Board(grid)


def test_env_runs_random_loop_without_crashing():
    board = _sample_board()
    env = SudokuGymEnv(board, max_steps=5)

    obs, info = env.reset()
    assert obs.shape == (board.size(), board.size(), board.size() + 1)
    assert info["action_mask"].shape == (board.size(), board.size(), board.size())

    for _ in range(3):
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (board.size(), board.size(), board.size() + 1)
        assert info["action_mask"].shape == (board.size(), board.size(), board.size())
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)

    # Garantia básica: truncamento respeita max_steps
    if env._max_steps is not None:  # noqa: SLF001 - acesso controlado para teste
        assert env._step_count <= env._max_steps

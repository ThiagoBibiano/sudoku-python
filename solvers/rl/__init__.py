"""Camada de RL (Reinforcement Learning) para Sudoku."""

from .env import RewardConfig, SudokuGymEnv
from .agent import SudokuNet, ResidualBlock
from .data import (
    SudokuCSVDataset,
    build_dataloader,
    encode_puzzle_one_hot,
    givens_mask,
    puzzle_str_to_grid,
)

__all__ = [
    "RewardConfig",
    "SudokuGymEnv",
    "SudokuCSVDataset",
    "build_dataloader",
    "encode_puzzle_one_hot",
    "givens_mask",
    "puzzle_str_to_grid",
    "SudokuNet",
    "ResidualBlock",
]

"""Camada de RL (Reinforcement Learning) para Sudoku."""

from .env import (
    RewardConfig,
    SudokuGymEnv,
    FlattenSudokuActionSpace,
    sudoku_action_mask,
)
from .agent import SudokuNet, ResidualBlock
from .callbacks import SudokuVisualizationCallback
from .data import (
    SudokuCSVDataset,
    build_dataloader,
    encode_puzzle_one_hot,
    givens_mask,
    puzzle_str_to_grid,
)
from .policy import SudokuMaskablePolicy, SudokuFeatureExtractor

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
    "FlattenSudokuActionSpace",
    "sudoku_action_mask",
    "SudokuVisualizationCallback",
    "SudokuMaskablePolicy",
    "SudokuFeatureExtractor",
]

"""Ambiente Gymnasium para RL em Sudoku.

Este módulo transforma `Board` + `SudokuRules` em um ambiente compatível
com Gymnasium/Stable-Baselines, expondo um espaço de observação one-hot
e máscara de ações para evitar jogadas ilegais.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import numpy as np

from core.board import Board
from core.rules import SudokuRules

try:  # Dependência opcional até o pipeline de RL estar configurado
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as exc:  # pragma: no cover - só executa sem gymnasium instalado
    gym = None
    spaces = None
    _GYM_IMPORT_ERROR = exc


Action = Tuple[int, int, int]


@dataclass
class RewardConfig:
    """Configurações de recompensa para o agente de RL."""

    valid_move: float = 0.1
    unit_complete: float = 1.0  # linha ou coluna completa
    box_complete: float = 1.0
    solved_bonus: float = 10.0
    invalid_move: float = -0.5
    step_penalty: float = -0.01


class SudokuGymEnv(gym.Env if gym is not None else object):
    """Ambiente Gymnasium que encapsula o tabuleiro de Sudoku.

    Observação:
        - Observação: tensor one-hot (size, size, size+1) com canal extra para givens.
        - Ação: MultiDiscrete([size, size, size]) → (linha, coluna, valor-1).
        - Máscara de ação: devolvida em `info["action_mask"]`.
    """

    metadata = {"render_modes": ["ansi"]}

    def __init__(
        self,
        board: Board,
        *,
        reward_cfg: Optional[RewardConfig] = None,
        max_steps: Optional[int] = None,
    ) -> None:
        if gym is None:
            raise ImportError(
                "gymnasium é obrigatório para usar SudokuGymEnv "
                f"(erro original: {_GYM_IMPORT_ERROR})"
            )
        super().__init__()
        self._initial_board = board.clone()
        self._board = board.clone()
        self._size = board.size()
        self._reward_cfg = reward_cfg or RewardConfig()
        self._max_steps = max_steps
        self._step_count = 0
        self.rules = SudokuRules()

        obs_shape = (self._size, self._size, self._size + 1)
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=obs_shape, dtype=np.float32
        )
        self.action_space = spaces.MultiDiscrete(
            [self._size, self._size, self._size]
        )

        self._required_digits = set(range(1, self._size + 1))

    # ------------------------------------------------------------------ #
    # API Gymnasium
    # ------------------------------------------------------------------ #
    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        super().reset(seed=seed)
        self._board = self._initial_board.clone()
        self._step_count = 0
        obs = self._encode_observation()
        info = {"action_mask": self._compute_action_mask()}
        return obs, info

    def step(
        self, action: Action
    ) -> Tuple[np.ndarray, float, bool, bool, Dict[str, Any]]:
        r, c, v_idx = self._normalize_action(action)
        value = v_idx + 1  # ação é zero-indexada; Sudoku vai de 1..size
        self._step_count += 1
        terminated = False
        truncated = False
        reward = 0.0

        if self._board.is_given(r, c):
            reward += self._reward_cfg.invalid_move
        elif self._board.get(r, c) != 0:
            reward += self._reward_cfg.invalid_move
        elif not self.rules.can_place(self._board, r, c, value):
            reward += self._reward_cfg.invalid_move
        else:
            self._board.set(r, c, value)
            reward += self._reward_cfg.valid_move
            reward += self._completion_bonus(r, c)
            if self.rules.is_solved(self._board):
                terminated = True
                reward += self._reward_cfg.solved_bonus
        reward += self._reward_cfg.step_penalty

        if self._max_steps is not None and self._step_count >= self._max_steps:
            truncated = not terminated

        obs = self._encode_observation()
        info = {"action_mask": self._compute_action_mask()}
        return obs, reward, terminated, truncated, info

    def render(self) -> str:
        """Retorna o tabuleiro como string (modo 'ansi')."""
        return str(self._board)

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #
    def _encode_observation(self) -> np.ndarray:
        """Converte o estado em tensor one-hot + canal de givens."""
        grid = self._board.to_grid()
        obs = np.zeros(
            (self._size, self._size, self._size + 1), dtype=np.float32
        )
        given_channel = self._size
        for r in range(self._size):
            for c in range(self._size):
                value = grid[r][c]
                if value > 0:
                    obs[r, c, value - 1] = 1.0
                if self._board.is_given(r, c):
                    obs[r, c, given_channel] = 1.0
        return obs

    def _compute_action_mask(self) -> np.ndarray:
        """Máscara booleana (size, size, size) de ações legais."""
        mask = np.zeros(
            (self._size, self._size, self._size), dtype=np.bool_
        )
        for r in range(self._size):
            for c in range(self._size):
                if self._board.is_given(r, c) or self._board.get(r, c) != 0:
                    continue
                for v in range(1, self._size + 1):
                    if self.rules.can_place(self._board, r, c, v):
                        mask[r, c, v - 1] = True
        return mask

    def _completion_bonus(self, r: int, c: int) -> float:
        bonus = 0.0
        if self._is_row_complete(r):
            bonus += self._reward_cfg.unit_complete
        if self._is_col_complete(c):
            bonus += self._reward_cfg.unit_complete
        if self._is_box_complete(r, c):
            bonus += self._reward_cfg.box_complete
        return bonus

    def _is_row_complete(self, r: int) -> bool:
        return {self._board.get(r, c) for c in range(self._size)} == self._required_digits

    def _is_col_complete(self, c: int) -> bool:
        return {self._board.get(r, c) for r in range(self._size)} == self._required_digits

    def _is_box_complete(self, r: int, c: int) -> bool:
        n = int(round(np.sqrt(self._size)))
        br = (r // n) * n
        bc = (c // n) * n
        box_vals = {
            self._board.get(rr, cc)
            for rr in range(br, br + n)
            for cc in range(bc, bc + n)
        }
        return box_vals == self._required_digits

    def _normalize_action(self, action: Action) -> Action:
        if len(action) != 3:
            raise ValueError(
                f"Ação deve ser (linha, coluna, valor-1); recebida: {action}"
            )
        r, c, v_idx = (int(action[0]), int(action[1]), int(action[2]))
        return r, c, v_idx

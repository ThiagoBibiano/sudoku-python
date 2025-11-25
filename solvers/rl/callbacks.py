"""Callbacks auxiliares para treino de RL (MaskablePPO)."""

from __future__ import annotations

from typing import Optional

import numpy as np

try:
    from stable_baselines3.common.callbacks import BaseCallback
except ImportError as exc:  # pragma: no cover - apenas quando sb3 não está instalado
    BaseCallback = object  # type: ignore[assignment]
    _SB3_IMPORT_ERROR = exc


class SudokuVisualizationCallback(BaseCallback):  # type: ignore[misc]
    """Callback simples para logar métricas e snapshots do tabuleiro."""

    def __init__(
        self,
        log_freq: int = 1_000,
        save_path: Optional[str] = None,
        save_freq: int = 50_000,
    ) -> None:
        if isinstance(BaseCallback, object) and not hasattr(BaseCallback, "_init_callback"):
            raise ImportError(
                "stable-baselines3 é obrigatório para usar SudokuVisualizationCallback "
                f"(erro original: {_SB3_IMPORT_ERROR})"
            )
        super().__init__()
        self.log_freq = log_freq
        self.save_path = save_path
        self.save_freq = save_freq

    def _on_step(self) -> bool:  # noqa: D401
        if self.num_timesteps % self.log_freq != 0:
            return True

        env = self.training_env
        base_env = None
        if hasattr(env, "envs"):
            base_env = env.envs[0]
        else:
            base_env = env
        if hasattr(base_env, "env"):
            base_env = base_env.env

        board_repr = None
        filled_ratio = None
        if hasattr(base_env, "render"):
            board_repr = base_env.render()
        if hasattr(base_env, "_board"):
            grid = base_env._board.to_grid()  # type: ignore[attr-defined]
            total = len(grid) * len(grid[0])
            non_zero = sum(1 for row in grid for v in row if v != 0)
            filled_ratio = non_zero / total if total else 0.0

        if board_repr is not None:
            self.logger.record("sudoku/board", board_repr)
        if filled_ratio is not None:
            self.logger.record("sudoku/filled_ratio", filled_ratio)

        if self.save_path and self.num_timesteps % self.save_freq == 0:
            path = f"{self.save_path}/model_{self.num_timesteps}"
            self.model.save(path)

        return True

"""Treino de MaskablePPO com SudokuGymEnv + action masking."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from core.board import Board
from solvers.rl.env import (
    FlattenSudokuActionSpace,
    SudokuGymEnv,
    sudoku_action_mask,
)
from solvers.rl.callbacks import SudokuVisualizationCallback
from solvers.rl.data import puzzle_str_to_grid
from solvers.rl.policy import SudokuMaskablePolicy

try:
    import torch
    from stable_baselines3.common.vec_env import DummyVecEnv
    from sb3_contrib.ppo_mask import MaskablePPO
    from sb3_contrib.common.wrappers import ActionMasker
except ImportError as exc:  # pragma: no cover - só avalia quando deps faltam
    raise ImportError(
        "Treino RL requer torch, stable-baselines3 e sb3-contrib instalados. "
        f"Erro original: {exc}"
    )


def load_board_from_csv(csv_path: str | Path, start_row: int = 0) -> Board:
    """Carrega um puzzle do CSV (linha específica)."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {csv_path}")
    with csv_path.open("r") as f:
        next(f)  # header
        for idx, line in enumerate(f):
            if idx < start_row:
                continue
            puzzle = line.strip().split(",")[0]
            grid = puzzle_str_to_grid(puzzle)
            return Board(grid)
    raise ValueError(f"Não foi possível ler puzzle na linha {start_row} de {csv_path}")


def make_env(csv_path: str | Path, max_steps: int, start_row: int = 0):
    def _init():
        board = load_board_from_csv(csv_path, start_row=start_row)
        env = SudokuGymEnv(board, max_steps=max_steps)
        env = FlattenSudokuActionSpace(env)
        env = ActionMasker(env, sudoku_action_mask)
        return env

    return _init


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treino RL com MaskablePPO + SudokuNet")
    parser.add_argument("--csv-path", type=str, default="data/rl_data/sudoku.csv")
    parser.add_argument("--pretrain-weights", type=str, default="policy_pretrain.pth")
    parser.add_argument("--total-timesteps", type=int, default=1_000_000)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--ent-coef", type=float, default=0.01)
    parser.add_argument("--gamma", type=float, default=0.99)
    parser.add_argument("--log-dir", type=str, default="runs/ppo_masked")
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--dropout-rate", type=float, default=0.1)
    parser.add_argument("--vec-envs", type=int, default=1)
    parser.add_argument("--start-row", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.log_dir, exist_ok=True)

    env_fns = [
        make_env(
            csv_path=args.csv_path,
            max_steps=args.max_steps,
            start_row=args.start_row + i,
        )
        for i in range(args.vec_envs)
    ]
    vec_env = DummyVecEnv(env_fns)

    model = MaskablePPO(
        SudokuMaskablePolicy,
        vec_env,
        learning_rate=args.learning_rate,
        ent_coef=args.ent_coef,
        gamma=args.gamma,
        tensorboard_log=args.log_dir,
    )

    # Carrega pesos supervisionados na feature extractor (SudokuNet)
    if Path(args.pretrain_weights).exists():
        state = torch.load(args.pretrain_weights, map_location="cpu")
        try:
            model.policy.features_extractor.net.load_state_dict(state, strict=False)
            print(f"✅ Pesos carregados de {args.pretrain_weights} na feature extractor.")
        except Exception as exc:  # pragma: no cover - carregamento pode falhar por shape
            print(f"⚠️ Não foi possível carregar pesos pré-treinados: {exc}")
    else:
        print(f"⚠️ Arquivo de pesos não encontrado: {args.pretrain_weights}")

    callback = SudokuVisualizationCallback(
        log_freq=1_000, save_path=args.log_dir, save_freq=50_000
    )

    model.learn(total_timesteps=args.total_timesteps, callback=callback)
    final_path = Path(args.log_dir) / "ppo_masked_final"
    model.save(final_path)
    print(f"🏁 Treino concluído. Modelo salvo em {final_path}")


if __name__ == "__main__":
    main()

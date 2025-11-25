"""Utilitários de inferência para usar o modelo de IA no app/UI."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from core.board import Board
from solvers.rl.agent import SudokuNet
from solvers.rl.env import SudokuGymEnv

try:
    import torch
    import torch.nn.functional as F
except ImportError as exc:  # pragma: no cover - só avaliado quando torch não existe
    torch = None
    F = None  # type: ignore[assignment]
    _TORCH_IMPORT_ERROR = exc


def _require_torch() -> None:
    if torch is None:
        raise ImportError(
            "torch é obrigatório para usar inferência de IA "
            f"(erro original: {_TORCH_IMPORT_ERROR})"
        )


def load_ai_model(
    weights_path: str,
    *,
    device: str = "cpu",
    dropout_rate: float = 0.0,
) -> SudokuNet:
    """Carrega o SudokuNet com pesos pré-treinados para inferência."""
    _require_torch()
    model = SudokuNet(dropout_rate=dropout_rate)
    map_loc = torch.device(device)
    state = torch.load(weights_path, map_location=map_loc)
    model.load_state_dict(state, strict=False)
    model.to(map_loc).eval()
    return model


def board_to_observation(board: Board) -> np.ndarray:
    """Converte um Board em observação one-hot (9,9,10) usando o ambiente."""
    env = SudokuGymEnv(board.clone())
    return env._encode_observation()  # noqa: SLF001 - uso controlado


def get_ai_probabilities(
    board: Board, model: SudokuNet, device: Optional[str] = None
) -> np.ndarray:
    """Retorna tensor (9,9,9) de probabilidades por célula."""
    _require_torch()
    obs = board_to_observation(board)
    obs_t = torch.from_numpy(obs).unsqueeze(0).to(device or model.output_conv.weight.device)  # type: ignore[arg-type]
    with torch.no_grad():
        logits = model(obs_t)
        probs = F.softmax(logits, dim=3)  # (1,9,9,9)
    return probs.cpu().squeeze(0).numpy()


def get_ai_hint(
    board: Board, model: SudokuNet, device: Optional[str] = None
) -> Tuple[int, int, int]:
    """Aplica máscara de ação e retorna a melhor jogada (r, c, valor)."""
    env = SudokuGymEnv(board.clone())
    action_mask = env.action_mask().astype(np.float32)  # (9,9,9)
    probabilities = get_ai_probabilities(board, model, device=device)
    masked_probs = probabilities * action_mask
    flat_idx = int(np.argmax(masked_probs))
    r, c, v_idx = np.unravel_index(flat_idx, masked_probs.shape)
    if masked_probs[r, c, v_idx] <= 0.0:
        return -1, -1, -1
    return r, c, v_idx + 1

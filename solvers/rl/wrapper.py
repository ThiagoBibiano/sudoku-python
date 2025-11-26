"""Adaptadores para conectar o agente de RL à interface de Solver."""

from __future__ import annotations

from typing import Optional

import numpy as np

from core.board import Board
from core.rules import SudokuRules
from solvers.base import Solver

try:
    import torch
except ImportError as exc:  # pragma: no cover - só avaliado quando torch não existe
    torch = None
    _TORCH_IMPORT_ERROR = exc

from .agent import SudokuNet
from .data import encode_puzzle_one_hot


class NeuralSolver(Solver):
    """Solver greedy baseado na rede supervisionada."""

    def __init__(self, model_path: str = "policy_pretrain.pth", device: str = "cpu") -> None:
        if torch is None:
            raise ImportError(
                "torch é obrigatório para usar NeuralSolver "
                f"(erro original: {_TORCH_IMPORT_ERROR})"
            )
        self.device = torch.device(device)
        self.model = SudokuNet().to(self.device)
        self.rules = SudokuRules()
        try:
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self._loaded = True
        except FileNotFoundError:
            print(
                f"⚠️ Pesos '{model_path}' não encontrados. NeuralSolver funcionará sem pré-treino."
            )
            self._loaded = False

    def solve(self, board: Board) -> Optional[Board]:
        grid = board.to_grid()
        inp = encode_puzzle_one_hot(grid).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(inp)
            preds = torch.argmax(logits, dim=3) + 1  # volta para 1..9
        preds_np: np.ndarray = preds.cpu().numpy()[0]

        solved_grid: list[list[int]] = []
        for r in range(board.size()):
            row: list[int] = []
            for c in range(board.size()):
                if board.is_given(r, c):
                    row.append(board.get(r, c))
                else:
                    row.append(int(preds_np[r][c]))
            solved_grid.append(row)

        candidate = Board(solved_grid)
        if self.rules.is_solved(candidate):
            return candidate
        return None

    def metrics(self) -> dict[str, bool]:
        return {"model_loaded": getattr(self, "_loaded", False)}

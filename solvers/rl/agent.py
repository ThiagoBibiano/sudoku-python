"""Arquitetura da política neural para Sudoku (supervisionado + RL).

Implementa uma rede totalmente convolucional com blocos residuais
mantendo a dimensionalidade 9x9 ao longo de todo o pipeline.
"""

from __future__ import annotations

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError as exc:  # pragma: no cover - só avaliado quando torch não existe
    torch = None
    nn = None  # type: ignore[assignment]
    F = None  # type: ignore[assignment]
    _TORCH_IMPORT_ERROR = exc


def _require_torch() -> None:
    if torch is None:
        raise ImportError(
            "torch é obrigatório para usar solvers de IA "
            f"(erro original: {_TORCH_IMPORT_ERROR})"
        )


class ResidualBlock(nn.Module):  # type: ignore[misc]
    """Bloco residual clássico com dropout espacial."""

    def __init__(self, channels: int, dropout_rate: float = 0.0) -> None:
        _require_torch()
        super().__init__()
        self.conv1 = nn.Conv2d(
            channels, channels, kernel_size=3, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(channels)
        self.dropout = nn.Dropout2d(p=dropout_rate)
        self.conv2 = nn.Conv2d(
            channels, channels, kernel_size=3, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(channels)

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":  # noqa: D401
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.dropout(out)
        out = self.bn2(self.conv2(out))
        out = out + residual
        return F.relu(out)


class SudokuNet(nn.Module):  # type: ignore[misc]
    """Rede neural para Sudoku (entrada 9x9x10 → saída 9x9x9)."""

    def __init__(
        self, num_blocks: int = 10, hidden_dim: int = 64, dropout_rate: float = 0.1
    ) -> None:
        _require_torch()
        super().__init__()
        self.hidden_dim = hidden_dim
        self.input_conv = nn.Sequential(
            nn.Conv2d(10, hidden_dim, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(hidden_dim),
            nn.ReLU(),
        )
        self.res_blocks = nn.ModuleList(
            [ResidualBlock(hidden_dim, dropout_rate) for _ in range(num_blocks)]
        )
        self.dropout_final = nn.Dropout2d(p=dropout_rate)
        self.output_conv = nn.Conv2d(hidden_dim, 9, kernel_size=1)

    def forward_features(self, x: "torch.Tensor") -> "torch.Tensor":
        """Retorna apenas o corpo convolucional (B, hidden, 9, 9)."""
        x = x.permute(0, 3, 1, 2)
        x = self.input_conv(x)
        for block in self.res_blocks:
            x = block(x)
        return x

    def forward(self, x: "torch.Tensor") -> "torch.Tensor":  # noqa: D401
        # Espera entrada (B, 9, 9, 10); converte para formato de conv2d
        x = self.forward_features(x)
        x = self.dropout_final(x)
        logits = self.output_conv(x)  # (B, 9, 9, 9) após permutar
        return logits.permute(0, 2, 3, 1)

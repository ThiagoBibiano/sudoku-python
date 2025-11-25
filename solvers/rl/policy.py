"""Política customizada para MaskablePPO preservando estrutura 9x9."""

from __future__ import annotations

from typing import Any

try:
    import torch
    import torch.nn as nn
    from sb3_contrib.common.maskable.policies import MaskableActorCriticPolicy
    from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
except ImportError as exc:  # pragma: no cover - usado apenas com deps instaladas
    torch = None  # type: ignore[assignment]
    nn = None  # type: ignore[assignment]
    MaskableActorCriticPolicy = object  # type: ignore[assignment]
    BaseFeaturesExtractor = object  # type: ignore[assignment]
    _SB3_IMPORT_ERROR = exc

from .agent import SudokuNet


def _require_rl_deps() -> None:
    if torch is None:
        raise ImportError(
            "stable-baselines3 e sb3-contrib são necessários para políticas RL "
            f"(erro original: {_SB3_IMPORT_ERROR})"
        )


class SudokuFeatureExtractor(BaseFeaturesExtractor):  # type: ignore[misc]
    """Extrator que reaproveita o corpo do SudokuNet e preserva canais."""

    def __init__(
        self, observation_space, dropout_rate: float = 0.0, hidden_dim: int = 64
    ) -> None:
        _require_rl_deps()
        obs_shape = observation_space.shape  # (size, size, channels)
        board_size = int(obs_shape[0])
        self.board_size = board_size
        self.hidden_dim = hidden_dim
        self.net = SudokuNet(hidden_dim=self.hidden_dim, dropout_rate=dropout_rate)
        # features_dim informado ao SB3 é flatten do mapa convolucional
        self._features_dim = self.hidden_dim * board_size * board_size
        super().__init__(observation_space, features_dim=self._features_dim)

    @property
    def features_dim(self) -> int:  # type: ignore[override]
        return self._features_dim

    def forward(self, obs: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        fmap = self.net.forward_features(obs)  # (B, hidden, size, size)
        return torch.flatten(fmap, start_dim=1)

    def feature_map_shape(self) -> tuple[int, int, int]:
        return (self.hidden_dim, self.board_size, self.board_size)


class SudokuHeads(nn.Module):  # type: ignore[misc]
    """Cabeças de política (conv 1x1) e valor (GAP + MLP) preservando 2D."""

    def __init__(
        self,
        hidden_dim: int,
        board_size: int,
        pi_channels: int = 9,
        vf_hidden: int = 128,
    ) -> None:
        super().__init__()
        self.hidden_dim = hidden_dim
        self.board_size = board_size
        self.pi_conv = nn.Conv2d(hidden_dim, pi_channels, kernel_size=1)
        self.vf_head = nn.Sequential(
            nn.Linear(hidden_dim, vf_hidden),
            nn.ReLU(),
            nn.Linear(vf_hidden, 1),
        )
        self.latent_dim_pi = pi_channels * board_size * board_size
        self.latent_dim_vf = 1

    def forward(self, features: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        # features: (B, hidden*size*size); reconstroi mapa
        bsz = features.shape[0]
        fmap = features.view(bsz, self.hidden_dim, self.board_size, self.board_size)

        pi_logits = self.pi_conv(fmap)  # (B, 9, size, size)
        latent_pi = torch.flatten(pi_logits, start_dim=1)

        gap = fmap.mean(dim=(2, 3))  # (B, hidden)
        latent_vf = self.vf_head(gap)  # (B, 1)
        return latent_pi, latent_vf


class SudokuMaskablePolicy(MaskableActorCriticPolicy):  # type: ignore[misc]
    """Política customizada que preserva estrutura 9x9 para MaskablePPO."""

    def __init__(
        self,
        *args: Any,
        dropout_rate: float = 0.1,
        hidden_dim: int = 64,
        **kwargs: Any,
    ) -> None:
        _require_rl_deps()
        features_extractor_class = kwargs.pop("features_extractor_class", SudokuFeatureExtractor)
        features_extractor_kwargs = kwargs.pop(
            "features_extractor_kwargs", {"dropout_rate": dropout_rate, "hidden_dim": hidden_dim}
        )
        super().__init__(
            *args,
            features_extractor_class=features_extractor_class,
            features_extractor_kwargs=features_extractor_kwargs,
            **kwargs,
        )

    def _build_mlp_extractor(self) -> None:
        extractor: SudokuFeatureExtractor = self.features_extractor  # type: ignore[assignment]
        hidden_dim = extractor.hidden_dim
        board_size = extractor.board_size
        self.mlp_extractor = SudokuHeads(hidden_dim, board_size)

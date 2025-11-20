"""Tipos auxiliares para solvers (Explain Mode, eventos, métricas)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from core.board import Board


@dataclass(frozen=True)
class StepEvent:
    """Evento emitido durante o modo de explicação do solver.

    Attributes:
        step_type: Tipo de passo (ex.: "assign", "backtrack", "finished").
        cell: Coordenada (linha, coluna) afetada por este passo.
        value: Valor associado à ação (0 representa limpar/backtrack).
        candidates: Candidatos considerados para a célula, se houver.
        reason: Texto curto explicando a escolha.
        board: Snapshot do board após aplicar o passo (para animação).
        depth: Profundidade atual da busca (0 = topo).
    """

    step_type: str
    cell: Optional[Tuple[int, int]]
    value: int
    candidates: Optional[Sequence[int]] = None
    reason: Optional[str] = None
    board: Optional[Board] = None
    depth: Optional[int] = None

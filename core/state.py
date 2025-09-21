"""Estado de resolução (State) e candidatos.

Responsabilidades:
- Encapsular o Board durante a resolução.
- Manter candidatos/domínios por célula (futuras etapas).
- Expor operações auxiliares à busca/propagação.

Nesta etapa, apenas a interface e docstrings.
"""

from __future__ import annotations
from typing import Optional
from .board import Board


class State:
    """Estado durante a resolução (busca/propagação).

    Attributes:
        board (Board): Tabuleiro atual.
    """

    def __init__(self, board: Board) -> None:
        """Inicializa o estado a partir de um Board.

        Args:
            board: Tabuleiro inicial (pode conter células vazias).
        """
        raise NotImplementedError

    def is_consistent(self) -> bool:
        """Verifica se o estado atual não viola regras básicas.

        Returns:
            True se consistente; False caso contrário.
        """
        raise NotImplementedError


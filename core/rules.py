"""Validação de regras do Sudoku (SudokuRules).

Responsabilidades:
- Verificar jogadas válidas em linhas, colunas e subgrades.
- Checar se um tabuleiro está resolvido.

Não deve alterar o estado do Board.
"""

from __future__ import annotations
from .types import Digit
from .board import Board


class SudokuRules:
    """Validador de regras do Sudoku.

    Fornece operações puras de checagem (sem mutar Board).
    """

    def can_place(self, board: Board, r: int, c: int, v: Digit) -> bool:
        """Verifica se é permitido colocar o dígito v na célula (r, c).

        Args:
            board: Instância do tabuleiro.
            r: Linha (0-index).
            c: Coluna (0-index).
            v: Dígito candidato (1..9).

        Returns:
            True se a jogada não viola regras; False caso contrário.
        """
        raise NotImplementedError

    def is_solved(self, board: Board) -> bool:
        """Indica se o tabuleiro está completamente resolvido.

        Args:
            board: Instância do tabuleiro.

        Returns:
            True se todas as células estão preenchidas e válidas.
        """
        raise NotImplementedError


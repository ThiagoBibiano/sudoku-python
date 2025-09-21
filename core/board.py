"""Representação de tabuleiro (Board).

Responsabilidades:
- Armazenar a grade (estado das células).
- Oferecer operações seguras de leitura/escrita (nesta etapa: assinaturas).
- Não validar regras (separação via SudokuRules).

Nesta etapa, mantenha apenas a interface (sem lógica).
"""

from __future__ import annotations
from typing import Optional
from .types import Grid, Digit, Coord, Size


class Board:
    """Contêiner de estado de um tabuleiro de Sudoku.

    Neste estágio, apenas defina a interface pública. A implementação
    virá em etapas seguintes.

    Attributes:
        _grid (Grid): Grade 2D do tabuleiro.
        _n (Size): Parâmetro N (3 para 9x9).
    """

    def __init__(self, grid: Grid, n: Size = 3) -> None:
        """Inicializa o tabuleiro.

        Args:
            grid: Grade inicial; use 0 para células vazias.
            n: Parâmetro N; N=3 => 9x9.
        """
        raise NotImplementedError

    def size(self) -> int:
        """Retorna o tamanho total da grade (N*N).

        Returns:
            Tamanho da dimensão da grade (ex.: 9).
        """
        raise NotImplementedError

    def get(self, r: int, c: int) -> Digit:
        """Obtém o valor na célula (r, c).

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).

        Returns:
            Dígito na célula; 0 indica vazio.
        """
        raise NotImplementedError

    def set(self, r: int, c: int, v: Digit) -> None:
        """Define o valor na célula (r, c).

        Atenção: a validação de regras NÃO é responsabilidade do Board.

        Args:
            r: Índice da linha.
            c: Índice da coluna.
            v: Dígito (0 para vazio).
        """
        raise NotImplementedError

    def clone(self) -> "Board":
        """Retorna uma cópia do tabuleiro.

        Returns:
            Nova instância de Board com a mesma grade.
        """
        raise NotImplementedError


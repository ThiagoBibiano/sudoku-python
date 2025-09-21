"""Representação de tabuleiro (Board).

Responsabilidades (nesta sub-etapa 2.1):
- Armazenar a grade recebida no construtor.
- Expor o tamanho lógico da grade via `size()`.

Não há validação de regras ou candidatos nesta etapa.
Validações mais completas e operações de leitura/escrita virão nas próximas sub-etapas.

Docstrings no formato Google Style, PEP8 e foco em OOP/SOLID.
"""

from __future__ import annotations
from typing import Sequence
from .types import Grid, Digit, Size, DEFAULT_N


class Board:
    """Contêiner de estado de um tabuleiro de Sudoku.

    Nesta sub-etapa, a classe mantém apenas o estado e o tamanho,
    sem implementar validações ou operações de leitura/escrita além
    da consulta do tamanho.

    Attributes:
        _grid (list[list[int]]): Grade 2D interna do tabuleiro.
        _n (int): Parâmetro N (3 para 9x9, 4 para 16x16, etc.).
        _size (int): Dimensão total da grade (N*N).
    """

    def __init__(self, grid: Grid, n: Size = DEFAULT_N) -> None:
        """Inicializa o tabuleiro com uma grade e parâmetro N.

        Realiza apenas cópia defensiva superficial da grade nesta etapa,
        sem validações profundas de dimensão ou faixa de dígitos.
        Validações completas serão adicionadas nas próximas sub-etapas.

        Args:
            grid: Grade inicial; use 0 para células vazias.
            n: Parâmetro N; N=3 => 9x9.

        Raises:
            ValueError: Se `n` for menor que 1.
        """
        if n < 1:
            raise ValueError("Parameter `n` must be >= 1.")
        self._n: int = int(n)
        self._size: int = self._n * self._n

        # Cópia defensiva superficial (linhas novas; elementos mantidos).
        # Validações de shape e faixa de valores virão depois.
        self._grid: list[list[int]] = [list(row) for row in grid]

    def size(self) -> int:
        """Retorna a dimensão da grade (N*N).

        Returns:
            int: Dimensão da grade (ex.: 9 para N=3).
        """
        return self._size

    # Os métodos abaixo serão implementados nas próximas sub-etapas:
    # - get(self, r: int, c: int) -> Digit
    # - set(self, r: int, c: int, v: Digit) -> None
    # - with_value(self, r: int, c: int, v: Digit) -> "Board"
    # - clone(self) -> "Board"
    # - to_grid(self) -> Grid
    # - is_full(self) -> bool
    # - __repr__/__str__


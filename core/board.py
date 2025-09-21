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

    Nesta fase, a classe mantém estado, expõe leitura e cópias,
    sem implementar escrita ou validações complexas.

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

    def get(self, r: int, c: int) -> Digit:
        """Obtém o valor na célula (r, c).

        Não realiza validação de regras; apenas acesso seguro
        com checagem de limites.

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).

        Returns:
            Dígito na célula; 0 indica vazio.

        Raises:
            IndexError: Se (r, c) estiver fora dos limites da grade.
        """
        if not (0 <= r < self._size) or not (0 <= c < self._size):
            raise IndexError(
                f"Cell index out of bounds: (r={r}, c={c}) for size {self._size}."
            )
        return self._grid[r][c]

    def to_grid(self) -> Grid:
        """Retorna uma cópia profunda da grade interna.

        Útil para serialização/IO e para evitar vazamento de referências.

        Returns:
            Grid: Nova lista de listas com os mesmos valores.
        """
        return [row.copy() for row in self._grid]

    def clone(self) -> "Board":
        """Cria uma cópia do tabuleiro (novo Board com a mesma grade e N).

        Returns:
            Board: Nova instância independente.
        """
        return Board(self.to_grid(), n=self._n)

    # -------------------------
    # Representações (depuração)
    # -------------------------

    def __repr__(self) -> str:
        """Representação detalhada para depuração.

        Returns:
            str: String com N, size e pequena prévia da grade.
        """
        preview_rows = 3 if self._size >= 3 else self._size
        preview = "; ".join(
            " ".join(str(v) for v in self._grid[r][: min(self._size, 6)])
            for r in range(preview_rows)
        )
        return f"Board(n={self._n}, size={self._size}, preview=[{preview}])"

    def __str__(self) -> str:
        """Representação amigável em múltiplas linhas.

        Substitui zeros por pontos para facilitar visualização
        sem confundir com dígitos válidos.

        Returns:
            str: Grade formatada linha a linha.
        """
        def fmt_row(row: list[int]) -> str:
            return " ".join(str(v) if v != 0 else "." for v in row)

        return "\n".join(fmt_row(row) for row in self._grid)


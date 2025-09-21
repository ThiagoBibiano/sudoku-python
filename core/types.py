"""Tipos básicos, aliases e constantes do projeto.

Centraliza aliases e constantes para melhorar legibilidade e facilitar
uma futura generalização para grades N² x N².

Docstrings no formato Google Style.
"""

from __future__ import annotations
from typing import Tuple, List

# ---------------------------------------------------------------------------
# Aliases de tipos
# ---------------------------------------------------------------------------

Digit = int
"""Inteiro representando um dígito do Sudoku. Valor 0 indica célula vazia."""

Coord = Tuple[int, int]
"""Coordenada (linha, coluna), 0-indexada, onde 0 ≤ linha,coluna < size."""

Grid = List[List[Digit]]
"""Grade 2D representando o tabuleiro; 0 representa célula vazia."""

Size = int
"""Tamanho base N do Sudoku (N=3 para 9x9, N=4 para 16x16, etc.)."""


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DEFAULT_N: Size = 3
"""Valor padrão de N. Para N=3, o tabuleiro é 9x9 (3² x 3²)."""

EMPTY: Digit = 0
"""Dígito reservado para representar célula vazia."""


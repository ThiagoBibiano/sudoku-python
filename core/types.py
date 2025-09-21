"""Tipos básicos e aliases do projeto.

Este módulo centraliza aliases de tipos para melhorar legibilidade e
permitir evolução futura (ex.: suportar N² x N²).
"""

from __future__ import annotations
from typing import Tuple, List, NewType

Digit = int
"""Inteiro representando um dígito válido do Sudoku (1..9)."""

Coord = Tuple[int, int]
"""Coordenada (linha, coluna), 0-indexada."""

Grid = List[List[Digit]]
"""Grade 2D representando o tabuleiro de Sudoku; 0 representa célula vazia."""

Size = int
"""Tamanho base N do Sudoku (N=3 para 9x9)."""


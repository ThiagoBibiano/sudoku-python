"""Contratos (ABCs) para solucionadores de Sudoku.

Fornece a interface mínima para plugar diferentes abordagens
(backtracking, DLX, CP-SAT, meta-heurísticas, IA).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
from ..core.board import Board


class Solver(ABC):
    """Contrato base para solucionadores de Sudoku.

    A implementação concreta deve respeitar o princípio de não mutar
    a instância de entrada diretamente, retornando uma nova solução
    ou None quando inaplicável.
    """

    @abstractmethod
    def solve(self, board: Board) -> Optional[Board]:
        """Resolve o tabuleiro.

        Args:
            board: Tabuleiro de entrada.

        Returns:
            Nova instância de Board com solução; None se não houver.
        """
        raise NotImplementedError


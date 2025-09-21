"""Validação de regras do Sudoku (SudokuRules).

Este módulo provê operações **puras** de verificação sobre um `Board`,
sem mutar estado. Ele não faz checagens de "pista inicial" (givens) e
não impõe políticas de escrita — esse controle pertence ao `Board`.
Aqui garantimos apenas as **regras do Sudoku**:

- Um dígito (1..size) pode ser colocado em (r, c) se **não** existir
  em sua **linha**, **coluna** e **subgrade** N×N correspondente.
- Um tabuleiro está **resolvido** se todas as células estiverem
  preenchidas (≠ 0) e **cada** linha, coluna e subgrade contiver
  exatamente os dígitos {1..size}, sem repetição.

A classe é parametrizada implicitamente pelo tamanho do board:
`size = n * n`. O valor de `n` é inferido de `size` (raiz perfeita).

Princípios aplicados:
- **SRP (Single Responsibility):** validação de regras separada do estado.
- **Open/Closed:** novas regras/técnicas podem ser adicionadas sem alterar
  a API pública.
"""

from __future__ import annotations

from math import isclose, sqrt
from typing import Iterable

from .types import Digit
from .board import Board


class SudokuRules:
    """Validador de regras do Sudoku.

    Esta classe expõe operações para:
    - verificar se um dígito pode ser colocado em (r, c) (`can_place`);
    - verificar se o tabuleiro está resolvido (`is_solved`);
    - checar consistência local/global (sem duplicatas) para debug/uso interno.

    Observação:
        - O dígito `0` representa célula vazia e **não** é considerado válido
          para `can_place` (use `0` apenas como "limpar célula" no `Board`).
    """

    # -------------------------
    # API pública
    # -------------------------

    def can_place(self, board: Board, r: int, c: int, v: Digit) -> bool:
        """Informa se colocar o dígito `v` em (r, c) respeita as regras.

        Não valida "pistas iniciais" (givens) nem aplica a jogada — apenas
        verifica a **legalidade** do valor conforme as regras do Sudoku.

        Args:
            board: Tabuleiro de entrada.
            r: Linha (0-index).
            c: Coluna (0-index).
            v: Dígito candidato (1..size). Valor 0 **não** é aceito.

        Returns:
            True se não houver o dígito `v` na mesma linha, coluna ou subgrade.

        Raises:
            IndexError: Se (r, c) estiver fora dos limites do tabuleiro.
            ValueError: Se `v` estiver fora de [1..size].
        """
        size = board.size()
        if v < 1 or v > size:
            raise ValueError(f"Digit must be in [1..{size}] (got {v}).")

        # Lê valor atual apenas para permitir "teste de posição" mesmo que a célula
        # já tenha `v` (útil para algumas rotinas). A regra proíbe duplicata nos
        # conjuntos, não "recolocar" o mesmo valor no próprio local.
        current = board.get(r, c)

        # Linha: v não pode existir em nenhuma outra célula da linha.
        for cc in range(size):
            if cc != c and board.get(r, cc) == v:
                return False

        # Coluna:
        for rr in range(size):
            if rr != r and board.get(rr, c) == v:
                return False

        # Subgrade:
        n = _infer_n_from_size(size)
        br = (r // n) * n
        bc = (c // n) * n
        for rr in range(br, br + n):
            for cc in range(bc, bc + n):
                if (rr != r or cc != c) and board.get(rr, cc) == v:
                    return False

        return True

    def is_solved(self, board: Board) -> bool:
        """Indica se o tabuleiro está completamente resolvido.

        Critérios:
        - Não há células vazias (0).
        - Cada linha contém exatamente {1..size}.
        - Cada coluna contém exatamente {1..size}.
        - Cada subgrade N×N contém exatamente {1..size}.

        Args:
            board: Tabuleiro de entrada.

        Returns:
            True se resolvido; False caso contrário.
        """
        size = board.size()
        required = _required_digits(size)

        # Linhas
        for r in range(size):
            row_vals = {board.get(r, c) for c in range(size)}
            if 0 in row_vals or row_vals != required:
                return False

        # Colunas
        for c in range(size):
            col_vals = {board.get(r, c) for r in range(size)}
            if 0 in col_vals or col_vals != required:
                return False

        # Subgrades
        n = _infer_n_from_size(size)
        for br in range(0, size, n):
            for bc in range(0, size, n):
                box_vals = {
                    board.get(r, c)
                    for r in range(br, br + n)
                    for c in range(bc, bc + n)
                }
                if 0 in box_vals or box_vals != required:
                    return False

        return True

    # -------------------------
    # Auxiliares (úteis em depuração e verificações locais)
    # -------------------------

    def is_cell_consistent(self, board: Board, r: int, c: int) -> bool:
        """Verifica se o valor atual em (r, c) não viola as regras locais.

        Útil para checagens rápidas: a célula é ZERO (vazia) ou, se não for,
        ela não duplica seu valor na linha/coluna/subgrade.

        Args:
            board: Tabuleiro.
            r: Linha (0-index).
            c: Coluna (0-index).

        Returns:
            True se a célula é vazia **ou** consistente com a vizinhança.
        """
        v = board.get(r, c)
        if v == 0:
            return True
        # Reaproveita can_place simulando a mesma posição.
        return self.can_place(board, r, c, v)

    def is_globally_consistent(self, board: Board) -> bool:
        """Checa se não existem duplicatas em nenhuma linha/coluna/subgrade.

        Diferente de `is_solved`, esta função ignora células vazias.
        Serve para validar que o estado atual é "possível".

        Args:
            board: Tabuleiro.

        Returns:
            True se nenhuma regra está sendo violada.
        """
        size = board.size()
        n = _infer_n_from_size(size)

        # Linhas
        for r in range(size):
            seen = set()
            for c in range(size):
                v = board.get(r, c)
                if v == 0:
                    continue
                if v in seen:
                    return False
                seen.add(v)

        # Colunas
        for c in range(size):
            seen = set()
            for r in range(size):
                v = board.get(r, c)
                if v == 0:
                    continue
                if v in seen:
                    return False
                seen.add(v)

        # Subgrades
        for br in range(0, size, n):
            for bc in range(0, size, n):
                seen = set()
                for r in range(br, br + n):
                    for c in range(bc, bc + n):
                        v = board.get(r, c)
                        if v == 0:
                            continue
                        if v in seen:
                            return False
                        seen.add(v)

        return True


# ========================================================================== #
# Funções auxiliares internas
# ========================================================================== #

def _infer_n_from_size(size: int) -> int:
    """Infere o parâmetro `n` a partir de `size = n * n`.

    Args:
        size: Dimensão da grade (ex.: 9, 16, 25).

    Returns:
        int: Valor de `n` (ex.: 3, 4, 5).

    Raises:
        ValueError: Se `size` não for um quadrado perfeito.
    """
    root = int(round(sqrt(size)))
    if root * root != size:
        raise ValueError(
            f"`size` must be a perfect square (got {size})."
        )
    return root


def _required_digits(size: int) -> set[int]:
    """Conjunto {1..size} usado em checagens de completude.

    Args:
        size: Dimensão da grade.

    Returns:
        set[int]: Dígitos esperados em linhas/colunas/subgrades.
    """
    return set(range(1, size + 1))


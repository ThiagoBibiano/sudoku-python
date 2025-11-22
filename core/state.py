"""Estado de resolução (State) e candidatos.

Responsabilidades:
- Encapsular o Board durante a resolução.
- Manter candidatos/domínios por célula (futuras etapas).
- Expor operações auxiliares à busca/propagação.

Nesta etapa, apenas a interface e docstrings.
"""

from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence, Set, Tuple

from .board import Board
from .rules import SudokuRules
from .types import EMPTY


class State:
    """Estado durante a resolução (busca/propagação).

    Attributes:
        board (Board): Tabuleiro atual.
        domains (Dict[Tuple[int, int], Set[int]]): Domínio de candidatos por célula.
    """

    def __init__(self, board: Board) -> None:
        """Inicializa o estado a partir de um Board, criando domínios."""
        self.board = board.clone()
        self._rules = SudokuRules()
        self.domains: Dict[Tuple[int, int], Set[int]] = {}
        self._initialize_domains()
        self.initial_prune()

    def is_consistent(self) -> bool:
        """Verifica se o estado atual não viola regras básicas.

        Returns:
            True se consistente; False caso contrário.
        """
        return self._rules.is_globally_consistent(self.board)

    def initial_prune(self) -> None:
        """Propaga valores iniciais, removendo candidatos dos vizinhos."""
        size = self.board.size()
        for r in range(size):
            for c in range(size):
                v = self.board.get(r, c)
                if v != EMPTY:
                    self._prune_peers(r, c, v)
        for coords, domain in self.domains.items():
            if not domain:
                raise ValueError(f"Domínio vazio em {coords}; puzzle inconsistente.")

    def assign(self, r: int, c: int, value: int) -> bool:
        """Atribui um valor e propaga remoções de candidatos.

        Retorna False se algum domínio ficar vazio (falha de consistência).
        """
        if (r, c) not in self.domains or value not in self.domains[(r, c)]:
            return False

        self._set_cell(r, c, value)

        queue = [(r, c, value)]
        while queue:
            cr, cc, val = queue.pop()
            for pr, pc in self._peers(cr, cc):
                if (pr, pc) == (cr, cc):
                    continue
                domain = self.domains[(pr, pc)]
                if val not in domain:
                    continue
                domain.discard(val)
                if not domain:
                    return False
                if len(domain) == 1 and self.board.get(pr, pc) == EMPTY:
                    sole = next(iter(domain))
                    self._set_cell(pr, pc, sole)
                    queue.append((pr, pc, sole))

        return True

    def clone(self) -> "State":
        """Retorna uma cópia profunda do estado (board + domínios)."""
        new_state = State(self.board.clone())
        new_state.domains = {k: set(v) for k, v in self.domains.items()}
        return new_state

    # ------------------------------------------------------------------ #
    # Internos
    # ------------------------------------------------------------------ #

    def _initialize_domains(self) -> None:
        """Cria domínios iniciais (tudo 1..N, ou valor único se preenchido)."""
        size = self.board.size()
        full_domain = set(range(1, size + 1))
        for r in range(size):
            for c in range(size):
                v = self.board.get(r, c)
                if v == EMPTY:
                    self.domains[(r, c)] = set(full_domain)
                else:
                    self.domains[(r, c)] = {v}

    def _set_cell(self, r: int, c: int, value: int) -> None:
        """Atualiza board e domínio de uma célula para valor fixo."""
        self.board = self.board.with_value(r, c, value)
        self.domains[(r, c)] = {value}

    def _prune_peers(self, r: int, c: int, value: int) -> None:
        """Remove 'value' das células vizinhas de (r, c)."""
        for pr, pc in self._peers(r, c):
            if (pr, pc) == (r, c):
                continue
            self.domains[(pr, pc)].discard(value)

    def _peers(self, r: int, c: int) -> Iterable[Tuple[int, int]]:
        """Gera coordenadas na mesma linha/coluna/caixa."""
        size = self.board.size()
        n = int(size ** 0.5)

        for cc in range(size):
            yield (r, cc)
        for rr in range(size):
            yield (rr, c)

        br = (r // n) * n
        bc = (c // n) * n
        for rr in range(br, br + n):
            for cc in range(bc, bc + n):
                yield (rr, cc)

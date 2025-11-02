"""Componentes de renderização do tabuleiro para Streamlit.

Este módulo NÃO implementa regras do Sudoku. Ele somente exibe e coleta
valores para edição, deixando a aplicação aplicar as mudanças no Board.
"""

from __future__ import annotations

from typing import List, Sequence

import streamlit as st

from core.board import Board
from core.types import EMPTY


def render_readonly_board(board: Board, *, box_dividers: bool = True) -> None:
    """Desenha o tabuleiro somente leitura (útil para preview)."""
    size = board.size()
    n = int(size ** 0.5)

    for r in range(size):
        cols = st.columns(size, gap="small")
        for c in range(size):
            v = board.get(r, c)
            label = str(v) if v != EMPTY else "·"
            cols[c].markdown(
                f"<div style='text-align:center; font-weight:600; font-size:1.05rem;"
                f"padding:0.2rem 0.1rem; border:1px solid #ddd;"
                f"{_cell_borders_css(r, c, n, box_dividers)}'>{label}</div>",
                unsafe_allow_html=True,
            )


def render_editable_matrix(
    board: Board,
    given_mask: Sequence[Sequence[bool]],
) -> List[List[int]]:
    """Desenha o tabuleiro editável e devolve a matriz proposta pelo usuário.

    Cada célula não-given recebe um widget de edição (selectbox 0..size),
    onde 0/· significa vazio. Células given são exibidas somente leitura.

    Args:
        board: Tabuleiro atual.
        given_mask: Máscara booleana de pistas iniciais.

    Returns:
        Matriz de inteiros com os valores propostos (0..size).
    """
    size = board.size()
    n = int(size ** 0.5)

    # Opções dos widgets (0 = vazio)
    options = ["·"] + [str(i) for i in range(1, size + 1)]

    proposed: List[List[int]] = []
    for r in range(size):
        cols = st.columns(size, gap="small")
        row_vals: List[int] = []
        for c in range(size):
            v = board.get(r, c)
            is_given = bool(given_mask[r][c])

            if is_given:
                label = str(v) if v != EMPTY else "·"
                cols[c].markdown(
                    f"<div style='text-align:center; font-weight:700; color:#333;"
                    f"background:#f3f3f3; border:1px solid #bbb; border-radius:6px;"
                    f"padding:0.25rem 0.1rem; {_cell_borders_css(r, c, n, True)}'>{label}</div>",
                    unsafe_allow_html=True,
                )
                row_vals.append(v)
            else:
                # Index da opção atual
                idx = 0 if v == EMPTY else v
                sel = cols[c].selectbox(
                    label=f"r{r}c{c}",
                    options=options,
                    index=idx,
                    key=f"cell_{r}_{c}",
                    label_visibility="hidden",
                )
                row_vals.append(0 if sel == "·" else int(sel))
        proposed.append(row_vals)
    return proposed


def _cell_borders_css(r: int, c: int, n: int, box_dividers: bool) -> str:
    """Gera CSS de bordas para destacar subgrades."""
    if not box_dividers:
        return ""
    css = []
    if r % n == 0:
        css.append("border-top:2px solid #666;")
    if c % n == 0:
        css.append("border-left:2px solid #666;")
    if (r + 1) % n == 0:
        css.append("border-bottom:2px solid #666;")
    if (c + 1) % n == 0:
        css.append("border-right:2px solid #666;")
    return " ".join(css)

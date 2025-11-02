# Em ui/components/board_view.py

from __future__ import annotations

from typing import List, Sequence

import streamlit as st

from core.board import Board
from core.types import EMPTY


# ----------------------------------------------------------------------
# CSS para estilizar o Board
# ----------------------------------------------------------------------

def _get_board_styles() -> str:
    """Retorna uma string com a tag <style> para injetar CSS."""
    return """
    <style>
        /* * Define o tamanho da célula como uma variável CSS.
         * Mude aqui para alterar o tamanho de todo o tabuleiro.
         */
        :root {
            --cell-size: 40px;
            --cell-gap: 2px;
        }

        /* Garante que colunas do Streamlit tenham gap mínimo */
        .stColumns {
            gap: var(--cell-gap) !important;
        }

        /* --- Células Read-Only e 'Given' (Divs) --- */
        /* Estas são usadas em st.markdown */

        .sudoku-cell-readonly, .sudoku-cell-given {
            width: var(--cell-size);
            height: var(--cell-size);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 1.25rem;
            font-weight: 600;
            border: 1px solid #ccc;
            border-radius: 4px;

            /* CHAVE: Garante que o width/height inclui o padding/border */
            box-sizing: border-box;
        }

        .sudoku-cell-given {
            font-weight: 700;
            color: #333;
            background-color: #eee;
            border: 1px solid #aaa;
        }

        /* --- Célula Editável (Input) --- */
        /* * O st.text_input cria um container (div) e um input (input).
         * Precisamos estilizar ambos.
         */

        /* 1. O container que o Streamlit cria (para st.text_input) */
        div[data-testid*="stTextInput"] {
            /* Remove qualquer padding que o Streamlit adiciona */
            padding: 0 !important;
            margin: 0;
            /* Garante que o container se ajuste ao input */
            width: var(--cell-size);
            height: var(--cell-size);
        }

        /* 2. O campo <input> dentro do st.text_input */
        div[data-testid*="stTextInput"] input {
            width: var(--cell-size);
            height: var(--cell-size);
            font-size: 1.3rem;
            text-align: center;
            border-radius: 4px;
            border-width: 2px;
            border-color: #007bff;
            color: #007bff;
            padding: 0; /* Remove padding interno do input */

            /* CHAVE: Garante que o width/height inclui o padding/border */
            box-sizing: border-box;
        }

        /* Oculta o label (r0c0, r0c1...) */
        div[data-testid*="stTextInput"] label {
            display: none;
        }
    </style>
    """

def _apply_board_styles() -> None:
    """Aplica o CSS customizado na página."""
    st.markdown(_get_board_styles(), unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Renderização (Modificada)
# ----------------------------------------------------------------------

def render_readonly_board(board: Board, *, box_dividers: bool = True) -> None:
    """Desenha o tabuleiro somente leitura (usando novo CSS)."""
    _apply_board_styles() # Aplica o CSS
    size = board.size()
    n = int(size ** 0.5)

    for r in range(size):
        cols = st.columns(size, gap="small")
        for c in range(size):
            v = board.get(r, c)
            label = str(v) if v != EMPTY else ""
            border_css = _cell_borders_css(r, c, n, box_dividers, is_readonly=True)

            cols[c].markdown(
                f"<div class='sudoku-cell-readonly' style='{border_css}'>{label}</div>",
                unsafe_allow_html=True,
            )


def render_editable_matrix(
    board: Board,
    given_mask: Sequence[Sequence[bool]],
) -> List[List[int]]:
    """Desenha o tabuleiro editável (usando st.text_input estilizado)."""
    _apply_board_styles() # Aplica o CSS
    size = board.size()
    n = int(size ** 0.5)

    proposed: List[List[int]] = []

    # Valores válidos (para validação do input)
    valid_chars = [str(i) for i in range(1, size + 1)]

    for r in range(size):
        cols = st.columns(size, gap="small")
        row_vals: List[int] = []
        for c in range(size):
            v = board.get(r, c)
            is_given = bool(given_mask[r][c])
            border_css = _cell_borders_css(r, c, n, True, is_readonly=is_given)

            if is_given:
                label = str(v) if v != EMPTY else ""
                cols[c].markdown(
                    f"<div class='sudoku-cell-given' style='{border_css}'>{label}</div>",
                    unsafe_allow_html=True,
                )
                row_vals.append(v)
            else:
                # Usar st.text_input em vez de st.selectbox
                # O valor atual é "" se EMPTY, ou str(v)
                current_val = str(v) if v != EMPTY else ""

                user_input = cols[c].text_input(
                    label=f"r{r}c{c}", # Label oculto pelo CSS
                    value=current_val,
                    max_chars=1, # Aceita apenas 1 dígito
                    key=f"cell_{r}_{c}",
                    label_visibility="hidden",
                )

                # Lógica para converter o input de volta para int
                val_to_store = EMPTY
                if user_input in valid_chars:
                    val_to_store = int(user_input)

                row_vals.append(val_to_store)

        proposed.append(row_vals)
    return proposed


def _cell_borders_css(r: int, c: int, n: int, box_dividers: bool, is_readonly: bool = False) -> str:
    """Gera CSS de bordas para destacar subgrades."""
    if not box_dividers:
        return ""

    # Ajusta a cor da borda grossa
    border_color = "#999" if is_readonly else "#333"

    css = []
    # Borda superior mais grossa a cada N linhas
    if r % n == 0 and r != 0:
        css.append(f"border-top: 2.5px solid {border_color};")
    # Borda esquerda mais grossa a cada N colunas
    if c % n == 0 and c != 0:
        css.append(f"border-left: 2.5px solid {border_color};")

    # Para garantir o fechamento das caixas 3x3 nas bordas externas
    if r == 0:
        css.append(f"border-top-width: 2.5px;")
    if c == 0:
        css.append(f"border-left-width: 2.5px;")
    if r == (n*n - 1):
        css.append(f"border-bottom-width: 2.5px;")
    if c == (n*n - 1):
        css.append(f"border-right-width: 2.5px;")

    return " ".join(css)

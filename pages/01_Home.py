"""Página Home do app Streamlit."""

from __future__ import annotations

import streamlit as st

from ui.state import (
    KEY_BOARD,
    KEY_BOARD_ID,
    KEY_BOARD_SOURCE,
    ensure_session_defaults,
)
from ui.components.board_view import render_readonly_board


def main() -> None:
    """Renderiza a página Home."""
    ensure_session_defaults()

    st.title("🏠 Home")
    st.write(
        "Use **Carregar (Load)** para importar um puzzle e **Jogar (Play)** para editar.\n\n"
        "A UI é fina: toda regra e estado vivem no core (`Board`, `SudokuRules`) e no `io`."
    )

    board = st.session_state[KEY_BOARD]
    if board is not None:
        st.subheader("Puzzle atual")
        meta = f"ID: `{st.session_state[KEY_BOARD_ID]}` — Fonte: `{st.session_state[KEY_BOARD_SOURCE]}`"
        st.caption(meta)
        render_readonly_board(board)
        st.page_link("pages/03_Play.py", label="Ir para Jogar (Play) →", icon="🎮")
    else:
        st.info("Nenhum puzzle carregado ainda.")
        st.page_link("pages/02_Load.py", label="Ir para Carregar (Load) →", icon="📥")


if __name__ == "__main__":
    main()

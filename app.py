"""Entrypoint do aplicativo Streamlit (multipáginas).

Este módulo apenas configura a aplicação e fornece atalhos de navegação.
As páginas ficam em `sudokku/ui/pages/`.

Execução:
    streamlit run sudokku/ui/app.py
"""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Renderiza a página inicial do app (launcher)."""
    st.set_page_config(
        page_title="Sudokku — MVP",
        page_icon="🧩",
        layout="centered",
        initial_sidebar_state="auto",
    )

    st.title("🧩 Sudokku — MVP Streamlit")
    st.write(
        "Bem-vindo! Use as páginas ao lado para **carregar** um puzzle e **jogar**.\n\n"
        "Este MVP separa **UI** de **lógica**: o app usa o `Board` e o `SudokuRules` "
        "do core, e o módulo `io` para carregar/salvar."
    )

    st.subheader("Navegação rápida")
    cols = st.columns(3)
    with cols[0]:
        st.page_link("pages/01_Home.py", label="Home", icon="🏠")
    with cols[1]:
        st.page_link("pages/02_Load.py", label="Carregar (Load)", icon="📥")
    with cols[2]:
        st.page_link("pages/03_Play.py", label="Jogar (Play)", icon="🎮")

    st.divider()
    st.page_link("pages/99_About.py", label="Sobre", icon="ℹ️")


if __name__ == "__main__":
    main()

"""Página de jogo/edição do puzzle atual."""

from __future__ import annotations

from typing import List

import streamlit as st

from core.io import to_json, to_txt_compact, to_txt_grid
from core.rules import SudokuRules
from core.types import EMPTY
from ui.components.board_view import render_editable_matrix
from ui.state import (
    KEY_BOARD,
    KEY_BOARD_ID,
    KEY_BOARD_SOURCE,
    KEY_GIVEN_MASK,
    KEY_NDJSON_ENTRIES,
    KEY_SELECTED_IDX,
    ensure_session_defaults,
    set_current_board,
)


def _apply_edits(proposed: List[List[int]]) -> None:
    """Aplica as edições do usuário ao board atual na sessão."""
    board = st.session_state[KEY_BOARD]
    given_mask = st.session_state[KEY_GIVEN_MASK]
    size = board.size()

    new_board = board  # pode ser substituído a cada mudança via with_value
    for r in range(size):
        for c in range(size):
            if given_mask[r][c]:
                continue  # pistas iniciais não podem mudar
            current = new_board.get(r, c)
            new_val = proposed[r][c]
            if new_val != current:
                # Atualiza de forma funcional para evitar efeitos colaterais
                new_board = new_board.with_value(r, c, new_val)

    # Reatribui mantendo id/origem e preservando máscara original
    set_current_board(
        new_board,
        board_id=st.session_state[KEY_BOARD_ID],
        source=st.session_state[KEY_BOARD_SOURCE],
    )


def _render_exporters() -> None:
    """Renderiza exportações (TXT/JSON) para o board atual."""
    board = st.session_state[KEY_BOARD]

    st.subheader("Exportar")
    tabs = st.tabs(["TXT (compacto, '0' vazio)", "TXT (grid, '.' vazio)", "JSON"])
    with tabs[0]:
        s = to_txt_compact(board, empty_char="0")
        st.code(s, language="text")
        st.download_button("Baixar .txt (compacto)", data=s, file_name="puzzle_compact.txt", mime="text/plain")
    with tabs[1]:
        s = to_txt_grid(board, empty_char=".")
        st.code(s, language="text")
        st.download_button("Baixar .txt (grid)", data=s, file_name="puzzle_grid.txt", mime="text/plain")
    with tabs[2]:
        s = to_json(board, include_n=True, pretty=True)
        st.code(s, language="json")
        st.download_button("Baixar .json", data=s, file_name="puzzle.json", mime="application/json")


def _render_navigation() -> None:
    """Navegação entre puzzles do NDJSON, se carregados."""
    entries = st.session_state[KEY_NDJSON_ENTRIES]
    if not entries:
        return

    st.subheader("Navegar no lote (NDJSON)")
    idx = st.session_state[KEY_SELECTED_IDX] or 0

    cols = st.columns(3)
    with cols[0]:
        prev = st.button("⬅️ Anterior", use_container_width=True)
    with cols[1]:
        st.write(f"Índice: {idx + 1}/{len(entries)}")
    with cols[2]:
        nxt = st.button("Próximo ➡️", use_container_width=True)

    if prev and idx > 0:
        idx -= 1
    if nxt and idx < len(entries) - 1:
        idx += 1

    if idx != (st.session_state[KEY_SELECTED_IDX] or 0):
        st.session_state[KEY_SELECTED_IDX] = idx
        entry = entries[idx]
        set_current_board(entry.board, board_id=entry.id, source="ndjson")
        st.success(f"Puzzle `{entry.id}` definido como atual.")


def main() -> None:
    """Renderiza a página Play."""
    ensure_session_defaults()

    st.title("🎮 Jogar (Play)")

    board = st.session_state[KEY_BOARD]
    given_mask = st.session_state[KEY_GIVEN_MASK]

    if board is None or given_mask is None:
        st.info("Carregue um puzzle na página **Load** antes de jogar.")
        st.page_link("pages/02_Load.py", label="Ir para Carregar (Load) →", icon="📥")
        return

    # Cabeçalho com metadados
    meta_cols = st.columns([2, 2, 3])
    meta_cols[0].metric("Dimensão", f"{board.size()} × {board.size()}")
    meta_cols[1].metric("ID", st.session_state[KEY_BOARD_ID] or "—")
    meta_cols[2].metric("Fonte", st.session_state[KEY_BOARD_SOURCE] or "—")

    st.caption("Células cinza são **pistas iniciais** (não editáveis). Selecione valores nas outras células.")

    # Board editável (coleta proposta de valores)
    proposed = render_editable_matrix(board, given_mask)

    cols = st.columns(3)
    with cols[0]:
        if st.button("Aplicar alterações", type="primary"):
            _apply_edits(proposed)
            st.success("Alterações aplicadas.")
    with cols[1]:
        rules = SudokuRules()
        if st.button("Validar regras"):
            ok = rules.is_globally_consistent(st.session_state[KEY_BOARD])
            if ok:
                st.success("Sem duplicatas em linhas/colunas/caixas.")
            else:
                st.error("Há violações das regras (duplicatas).")
    with cols[2]:
        if st.button("Limpar células editáveis"):
            # Define 0 em todas as células não-given
            size = board.size()
            cleared = board
            for r in range(size):
                for c in range(size):
                    if not given_mask[r][c] and cleared.get(r, c) != EMPTY:
                        cleared = cleared.with_value(r, c, EMPTY)
            set_current_board(
                cleared,
                board_id=st.session_state[KEY_BOARD_ID],
                source=st.session_state[KEY_BOARD_SOURCE],
            )
            st.success("Células editáveis limpas.")

    st.divider()
    _render_exporters()

    st.divider()
    _render_navigation()


if __name__ == "__main__":
    main()

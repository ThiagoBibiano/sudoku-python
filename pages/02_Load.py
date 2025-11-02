"""Página de carregamento de puzzles (unitário e NDJSON)."""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from core.io import parse_json, parse_ndjson, parse_txt_compact, parse_txt_grid
from core.rules import SudokuRules
from ui.state import (
    KEY_NDJSON_ENTRIES,
    KEY_SELECTED_IDX,
    ensure_session_defaults,
    set_current_board,
    clear_session_board,
    set_message,
)


def _handle_unit_load() -> None:
    """Seção para carregar puzzle unitário (TXT/JSON)."""
    st.subheader("Unitário (TXT/JSON)")

    uploaded = st.file_uploader(
        "Selecione um arquivo TXT (compacto ou grade) ou JSON (objeto).",
        type=["txt", "json"],
        accept_multiple_files=False,
        key="unit_uploader",
    )
    if not uploaded:
        return

    fmt = st.radio(
        "Formato do TXT:",
        options=["Auto (detectar)", "TXT compacto (81 chars)", "TXT grade (linhas)", "JSON (objeto)"],
        index=0,
        horizontal=True,
    )

    data = uploaded.read().decode("utf-8", errors="strict")

    try:
        if fmt.startswith("JSON"):
            board = parse_json(data)
        elif fmt.startswith("TXT compacto"):
            board = parse_txt_compact(data)
            # mesmo se vier com quebras, o parser acusará erro, mantendo clareza
        elif fmt.startswith("TXT grade"):
            board = parse_txt_grid(data, flex=True)
        else:
            # Auto: tenta compacto > grade
            try:
                board = parse_txt_compact(data)
            except Exception:
                board = parse_txt_grid(data, flex=True)

        set_current_board(board, board_id=None, source="unit")

        # Verificação básica
        rules = SudokuRules()
        ok = rules.is_globally_consistent(board)
        if ok:
            st.success("Puzzle unitário carregado com sucesso e consistente.")
            st.page_link("pages/03_Play.py", label="Ir para Jogar (Play) →", icon="🎮")
        else:
            st.warning("Puzzle carregado, mas há inconsistências nas regras (linhas/colunas/caixas).")
    except Exception as exc:  # noqa: BLE001 (aqui é UI: exibir erro genérico)
        st.error(f"Falha ao carregar puzzle unitário: {exc}")


def _handle_ndjson_load() -> None:
    """Seção para carregar puzzles NDJSON (lote por dificuldade)."""
    st.subheader("NDJSON (lote por dificuldade)")
    uploaded = st.file_uploader(
        "Selecione um arquivo NDJSON (um JSON por linha).",
        type=["ndjson"],
        accept_multiple_files=False,
        key="ndjson_uploader",
    )
    if not uploaded:
        return

    try:
        text = uploaded.read().decode("utf-8", errors="strict")
        entries = parse_ndjson(text)
        st.session_state[KEY_NDJSON_ENTRIES] = entries
        st.session_state[KEY_SELECTED_IDX] = 0 if entries else None

        if not entries:
            st.warning("Arquivo NDJSON não contém puzzles.")
            return

        st.success(f"{len(entries)} puzzles carregados.")
        _render_entries_selector(entries)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Falha ao carregar NDJSON: {exc}")


def _render_entries_selector(entries) -> None:
    """Tabela/selector para escolher um puzzle do NDJSON e definir como atual."""
    ids = [e.id for e in entries]
    idx = st.session_state[KEY_SELECTED_IDX]

    st.write("Selecione um puzzle:")
    new_idx = st.selectbox("ID do puzzle", options=list(range(len(ids))), format_func=lambda i: ids[i], index=idx or 0)

    if new_idx != idx:
        st.session_state[KEY_SELECTED_IDX] = new_idx

    if st.button("Definir como atual", type="primary"):
        entry = entries[new_idx]
        set_current_board(entry.board, board_id=entry.id, source="ndjson")
        st.success(f"Puzzle `{entry.id}` definido como atual.")
        st.page_link("pages/03_Play.py", label="Ir para Jogar (Play) →", icon="🎮")


def main() -> None:
    """Renderiza a página Load."""
    ensure_session_defaults()

    st.title("📥 Carregar (Load)")

    with st.expander("Carregar puzzle unitário (TXT/JSON)", expanded=True):
        _handle_unit_load()

    with st.expander("Carregar lote NDJSON (um por linha)", expanded=True):
        _handle_ndjson_load()

    st.divider()
    if st.button("Limpar puzzle atual", type="secondary"):
        clear_session_board()
        set_message("Puzzle atual limpo.")
        st.success("Session limpa (board e metadados).")


if __name__ == "__main__":
    main()

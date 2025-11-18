"""Página de jogo/edição do puzzle atual."""

from __future__ import annotations

from typing import Dict, List

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
    update_current_board,
)


def compute_completion_stats(board) -> Dict:
    """Conta linhas, colunas e caixas completas do board atual."""

    size = board.size()
    if size <= 0:
        return {"rows": 0, "cols": 0, "boxes": 0, "size": size, "boxes_total": 0}

    n = int(size ** 0.5)
    boxes_total = n * n
    expected = set(range(1, size + 1))

    def is_complete(values: List[int]) -> bool:
        return all(v != EMPTY for v in values) and set(values) == expected

    rows_complete = 0
    cols_complete = 0
    boxes_complete = 0

    for r in range(size):
        row_values = [board.get(r, c) for c in range(size)]
        if is_complete(row_values):
            rows_complete += 1

    for c in range(size):
        col_values = [board.get(r, c) for r in range(size)]
        if is_complete(col_values):
            cols_complete += 1

    for br in range(0, size, n):
        for bc in range(0, size, n):
            box_values = [
                board.get(r, c)
                for r in range(br, br + n)
                for c in range(bc, bc + n)
            ]
            if is_complete(box_values):
                boxes_complete += 1

    return {
        "rows": rows_complete,
        "cols": cols_complete,
        "boxes": boxes_complete,
        "size": size,
        "boxes_total": boxes_total,
    }


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

    update_current_board(new_board)


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
    """Renderiza a página Play (com atualização e validação automáticas)."""
    ensure_session_defaults()

    st.title("🎮 Jogar (Play)")

    board = st.session_state[KEY_BOARD]
    given_mask = st.session_state[KEY_GIVEN_MASK]

    if board is None or given_mask is None:
        st.info("Carregue um puzzle na página **Load** antes de jogar.")
        st.page_link("pages/02_Load.py", label="Ir para Carregar (Load) →", icon="📥")
        return

    completion_stats = compute_completion_stats(board)

    # Cabeçalho com metadados
    meta_cols = st.columns([2, 2, 3])
    meta_cols[0].metric("Dimensão", f"{board.size()} × {board.size()}")
    meta_cols[1].metric("ID", st.session_state[KEY_BOARD_ID] or "—")
    meta_cols[2].metric("Fonte", st.session_state[KEY_BOARD_SOURCE] or "—")

    st.caption("Células cinza são pistas iniciais. Digite 1-9 nas células azuis e pressione Enter.")

    progress_cols = st.columns(3)
    progress_data = [
        ("Linhas completas", completion_stats["rows"], completion_stats["size"]),
        ("Colunas completas", completion_stats["cols"], completion_stats["size"]),
        ("Caixas completas", completion_stats["boxes"], completion_stats["boxes_total"]),
    ]

    for col, (label, value, total) in zip(progress_cols, progress_data):
        col.metric(label, f"{value}/{total}")
        fraction = value / total if total else 0.0
        col.progress(fraction)

    # --- INÍCIO DA MODIFICAÇÃO PRINCIPAL ---

    # 1. Renderiza o board e coleta as propostas (como antes)
    proposed = render_editable_matrix(board, given_mask)

    # 2. APLICA AS ALTERAÇÕES IMEDIATAMENTE (sem botão)
    #    Toda vez que o usuário pressiona "Enter" em uma célula,
    #    o script re-executa, 'proposed' contém o novo valor,
    #    e _apply_edits atualiza o session_state.
    _apply_edits(proposed)

    # 3. VALIDA O NOVO ESTADO IMEDIATAMENTE (sem botão)
    #    Pega o board recém-atualizado do session_state
    current_board = st.session_state[KEY_BOARD]
    rules = SudokuRules()

    # Cria um container para a mensagem de status
    status_placeholder = st.empty()

    if not rules.is_globally_consistent(current_board):
        status_placeholder.error("❌ Há violações das regras (duplicatas detectadas).")
    else:
        # Se for consistente, verifica se está resolvido
        if current_board.is_full():
            if rules.is_solved(current_board):
                status_placeholder.success("🎉 Parabéns! Puzzle resolvido com sucesso!")
                st.balloons()
            else:
                # Caso raro: cheio, consistente, mas não resolvido (ex: faltam regras)
                status_placeholder.warning("Puzzle preenchido, mas algo está incorreto.")
        else:
            status_placeholder.info("✅ Tudo certo. Continue jogando.")

    # --- FIM DA MODIFICAÇÃO PRINCIPAL ---

# Botão de Limpar (este ainda é útil)
    if st.button("Limpar células editáveis"):
        # Pega o board e mask ATUAIS da sessão
        board = st.session_state[KEY_BOARD]
        given_mask = st.session_state[KEY_GIVEN_MASK]
        size = board.size()

        cleared = board
        # Itera para criar um novo board com as células limpas
        for r in range(size):
            for c in range(size):
                if not given_mask[r][c] and cleared.get(r, c) != EMPTY:
                    # A correção em core/board.py garante que with_value funciona
                    cleared = cleared.with_value(r, c, EMPTY)

        # 1. Usar a função 'update' que não mexe na given_mask
        update_current_board(cleared)

        st.success("Células editáveis limpas.")

        # 2. FORÇAR RE-EXECUÇÃO
        # Isso é essencial para que o render_editable_matrix
        # pegue o 'cleared' board do session_state na próxima execução.
        st.rerun()

    st.divider()
    _render_exporters()

    st.divider()
    _render_navigation()


if __name__ == "__main__":
    main()

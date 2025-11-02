"""Utilitários de estado da sessão para o app Streamlit.

Mantém um contrato simples de chaves em `st.session_state` para não
espalhar condicionais e valores padrão pelas páginas.
"""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from core.board import Board
from core.types import EMPTY


# -------------------------
# Chaves padronizadas
# -------------------------

KEY_BOARD = "board"
KEY_BOARD_ID = "board_id"
KEY_BOARD_SOURCE = "board_source"  # {"unit", "ndjson"} | None
KEY_NDJSON_ENTRIES = "ndjson_entries"  # list[PuzzleEntry]
KEY_SELECTED_IDX = "selected_entry_idx"  # int | None
KEY_GIVEN_MASK = "given_mask"  # list[list[bool]] (imutável durante a edição)
KEY_MESSAGE = "message"  # str | None


def ensure_session_defaults() -> None:
    """Garante que todas as chaves da sessão existam com defaults."""
    ss = st.session_state
    ss.setdefault(KEY_BOARD, None)
    ss.setdefault(KEY_BOARD_ID, None)
    ss.setdefault(KEY_BOARD_SOURCE, None)
    ss.setdefault(KEY_NDJSON_ENTRIES, [])
    ss.setdefault(KEY_SELECTED_IDX, None)
    ss.setdefault(KEY_GIVEN_MASK, None)
    ss.setdefault(KEY_MESSAGE, None)


def compute_given_mask(board: Board) -> List[List[bool]]:
    """Cria a máscara de 'pistas iniciais' a partir do grid atual.

    Args:
        board: Tabuleiro de referência.

    Returns:
        Matriz booleana (True = célula é pista inicial).
    """
    grid = board.to_grid()
    return [[cell != EMPTY for cell in row] for row in grid]


def set_current_board(board: Board, *, board_id: Optional[str] = None, source: Optional[str] = None) -> None:
    """Define o board atual na sessão e congela a máscara de pistas iniciais.

    Esta função **preserva** a máscara de 'givens' para evitar que jogadas
    subsequentes passem a ser consideradas 'givens' por engano.

    Args:
        board: Tabuleiro a definir.
        board_id: Identificador (opcional), por exemplo do NDJSON.
        source: Origem do puzzle (ex.: "unit" ou "ndjson").
    """
    st.session_state[KEY_BOARD] = board
    st.session_state[KEY_BOARD_ID] = board_id
    st.session_state[KEY_BOARD_SOURCE] = source
    st.session_state[KEY_GIVEN_MASK] = compute_given_mask(board)


def update_current_board(board: Board) -> None:
    """Atualiza APENAS o board na sessão, preservando a máscara de 'givens'.

    Esta função DEVE ser usada durante o jogo (ex: Play) para
    não tratar jogadas do usuário como novas 'givens'.
    """
    st.session_state[KEY_BOARD] = board


def clear_session_board() -> None:
    """Remove o board e metadados da sessão."""
    st.session_state[KEY_BOARD] = None
    st.session_state[KEY_BOARD_ID] = None
    st.session_state[KEY_BOARD_SOURCE] = None
    st.session_state[KEY_GIVEN_MASK] = None


def set_message(msg: Optional[str]) -> None:
    """Ajusta a mensagem de feedback na sessão (ou limpa)."""
    st.session_state[KEY_MESSAGE] = msg

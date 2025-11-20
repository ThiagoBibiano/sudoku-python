"""Página de resolução automática do puzzle atual via solver registrado."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple

import streamlit as st

import solvers  # noqa: F401 - importa para registrar solvers no registry
from core.rules import SudokuRules
from ui.components.board_view import render_readonly_board
from ui.state import (
    KEY_BOARD,
    KEY_BOARD_ID,
    KEY_BOARD_SOURCE,
    ensure_session_defaults,
    update_current_board,
)
from solvers.registry import all_registered


# Chaves internas para persistir o resultado da execução do solver.
SOLVE_ATTEMPTED = "solve_attempted"
SOLVE_SOLVER = "solve_solver_name"
SOLVE_BOARD = "solve_board"
SOLVE_ERROR = "solve_error"
SOLVE_METRICS = "solve_metrics"


def _ensure_solver_state_defaults() -> None:
    """Cria chaves de sessão usadas nesta página."""
    ss = st.session_state
    ss.setdefault(SOLVE_ATTEMPTED, False)
    ss.setdefault(SOLVE_SOLVER, None)
    ss.setdefault(SOLVE_BOARD, None)
    ss.setdefault(SOLVE_ERROR, None)
    ss.setdefault(SOLVE_METRICS, None)


def _clear_solver_result() -> None:
    """Reseta somente o resultado do solver (preserva seleção do widget)."""
    st.session_state[SOLVE_ATTEMPTED] = False
    st.session_state[SOLVE_BOARD] = None
    st.session_state[SOLVE_ERROR] = None
    st.session_state[SOLVE_METRICS] = None


def _run_solver(solver_name: str) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Executa o solver escolhido sobre o board atual."""
    registry = all_registered()
    solver_cls = registry[solver_name]
    solver = solver_cls()

    board = st.session_state[KEY_BOARD]
    solved_board = solver.solve(board.clone())

    metrics: Optional[Dict[str, Any]] = None
    metrics_fn = getattr(solver, "metrics", None)
    if callable(metrics_fn):
        metrics_obj = metrics_fn()
        try:
            metrics = asdict(metrics_obj)
        except TypeError:
            metrics = metrics_obj  # type: ignore[assignment]

    return solved_board, metrics


def _render_results() -> None:
    """Mostra o resultado mais recente do solver."""
    attempted = st.session_state[SOLVE_ATTEMPTED]
    solved_board = st.session_state[SOLVE_BOARD]
    solver_name = st.session_state[SOLVE_SOLVER]
    last_error = st.session_state[SOLVE_ERROR]
    metrics = st.session_state[SOLVE_METRICS]
    current_board = st.session_state[KEY_BOARD]

    if last_error:
        st.error(f"Falha ao executar o solver: {last_error}")
        return

    if not attempted:
        return

    if solved_board is None:
        st.warning(f"O solver `{solver_name}` não encontrou solução para o puzzle atual.")
        return

    rules = SudokuRules()
    solved_ok = rules.is_solved(solved_board)

    status_msg = "Solução encontrada."
    if solved_ok:
        st.success(f"{status_msg} Solver `{solver_name}` validou o tabuleiro.")
    else:
        st.warning(f"{status_msg} Porém a validação detectou inconsistências.")

    if metrics:
        st.subheader("Métricas do solver")
        st.json(metrics)

    view_cols = st.columns(2)
    with view_cols[0]:
        st.caption("Estado atual")
        render_readonly_board(current_board)
    with view_cols[1]:
        st.caption("Solução proposta")
        render_readonly_board(solved_board)

    st.divider()
    if st.button("Usar solução no Play", type="primary"):
        update_current_board(solved_board)
        st.success("Solução aplicada. Abra a página Jogar (Play) para explorar.")
        st.page_link("pages/03_Play.py", label="Ir para Jogar (Play) →", icon="🎮")


def main() -> None:
    """Renderiza a página Solve."""
    ensure_session_defaults()
    _ensure_solver_state_defaults()

    st.title("🧠 Resolver (Solve)")
    board = st.session_state[KEY_BOARD]

    if board is None:
        st.info("Carregue ou monte um puzzle na página **Load** antes de resolver.")
        st.page_link("pages/02_Load.py", label="Ir para Carregar (Load) →", icon="📥")
        return

    registry = all_registered()
    if not registry:
        st.error("Nenhum solver registrado no sistema.")
        return

    solver_names = sorted(registry.keys())
    default_idx = 0
    if st.session_state[SOLVE_SOLVER] in solver_names:
        default_idx = solver_names.index(st.session_state[SOLVE_SOLVER])

    st.selectbox(
        "Escolha o solver para usar",
        options=solver_names,
        index=default_idx,
        key=SOLVE_SOLVER,
        help="A lista vem do registro central de solvers.",
    )

    meta_cols = st.columns([2, 2, 2])
    meta_cols[0].metric("Dimensão", f"{board.size()}×{board.size()}")
    meta_cols[1].metric("ID", st.session_state[KEY_BOARD_ID] or "—")
    meta_cols[2].metric("Fonte", st.session_state[KEY_BOARD_SOURCE] or "—")

    action_cols = st.columns([1, 1, 1])
    run_clicked = action_cols[0].button("Resolver", type="primary")
    clear_clicked = action_cols[2].button("Limpar resultado", type="secondary")

    if clear_clicked:
        _clear_solver_result()

    if run_clicked:
        _clear_solver_result()  # limpa antes de nova execução
        solver_name = st.session_state[SOLVE_SOLVER] or solver_names[0]

        try:
            with st.spinner(f"Executando solver '{solver_name}'..."):
                solved_board, metrics = _run_solver(solver_name)

            st.session_state[SOLVE_ATTEMPTED] = True
            st.session_state[SOLVE_BOARD] = solved_board
            st.session_state[SOLVE_METRICS] = metrics
        except Exception as exc:  # noqa: BLE001
            st.session_state[SOLVE_ATTEMPTED] = True
            st.session_state[SOLVE_ERROR] = str(exc)

        st.rerun()

    _render_results()


if __name__ == "__main__":
    main()

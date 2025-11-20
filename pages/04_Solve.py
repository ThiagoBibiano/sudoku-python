"""Página de resolução automática do puzzle atual via solver registrado."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional, Tuple
import time

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
SOLVE_STOP = "solve_stop_requested"

SOLVER_EXPLANATIONS = {
    "backtracking": """
    ### 🐢 Backtracking (Padrão)
    **Estratégia: Tentativa e Erro (Força Bruta Inteligente)**

    Este algoritmo explora o tabuleiro como um labirinto:
    1. **Escolhe** a primeira célula vazia que encontra.
    2. **Tenta** colocar o número 1. Se as regras permitirem, avança.
    3. **Recua (Backtrack)** se chegar a um beco sem saída (nenhum número serve), voltando à célula anterior para trocar o valor.

    **Resumo:** Garante encontrar a solução, mas pode ser lento pois "chuta" valores sem analisar qual célula é mais crítica.
    """,
    "heuristic_backtracking": """
    ### 🐇 Backtracking com Heurísticas (MRV + LCV)
    **Estratégia: Ordem Otimizada de Escolha**

    Usa o mesmo motor do Backtracking, mas com duas "bússolas" para decidir o próximo passo:

    1. **MRV (Minimum Remaining Values):** Responde *"Qual célula preencher?"*.
       - Escolhe a célula com **menos candidatos possíveis**. Se uma célula só aceita o número '7', preenchemos ela agora para evitar erros futuros. ("Falhar primeiro").

    2. **LCV (Least Constraining Value):** Responde *"Qual número testar?"*.
       - Escolhe o número que elimina **menos opções** dos vizinhos. Tentamos deixar o caminho aberto para as outras células.

    **Resumo:** Reduz drasticamente a árvore de busca ao atacar os gargalos do problema primeiro.
    """,
    "forward_checking": """
    ### ✂️ Forward Checking (Propagação de Domínios)
    **Estratégia: Cortar o mal pela raiz**

    Em vez de apenas testar valores, este método **gerencia candidatos** de cada célula:
    - Mantém um domínio (lista de opções) para cada célula.
    - Ao atribuir um valor, remove-o automaticamente dos vizinhos (linha, coluna, caixa).
    - Se algum vizinho ficar sem opções, sabemos imediatamente que a escolha foi ruim e voltamos (backtrack) cedo.

    **Resumo:** Detecta falhas antes de aprofundar a busca, reduzindo chutes desnecessários.
    """,
}


def _ensure_solver_state_defaults() -> None:
    """Cria chaves de sessão usadas nesta página."""
    ss = st.session_state
    ss.setdefault(SOLVE_ATTEMPTED, False)
    ss.setdefault(SOLVE_SOLVER, None)
    ss.setdefault(SOLVE_BOARD, None)
    ss.setdefault(SOLVE_ERROR, None)
    ss.setdefault(SOLVE_METRICS, None)
    ss.setdefault(SOLVE_STOP, False)


def _clear_solver_result() -> None:
    """Reseta somente o resultado do solver (preserva seleção do widget)."""
    st.session_state[SOLVE_ATTEMPTED] = False
    st.session_state[SOLVE_BOARD] = None
    st.session_state[SOLVE_ERROR] = None
    st.session_state[SOLVE_METRICS] = None
    st.session_state[SOLVE_STOP] = False


def _run_solver(solver_name: str) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Executa o solver escolhido sobre o board atual."""
    registry = all_registered()
    solver_cls = registry[solver_name]
    solver = solver_cls()

    board = st.session_state[KEY_BOARD]
    solved_board = solver.solve(board.clone())

    metrics = _extract_metrics(solver)

    return solved_board, metrics


def _extract_metrics(solver: Any) -> Optional[Dict[str, Any]]:
    """Converte métricas do solver para dicionário, se disponível."""
    metrics_fn = getattr(solver, "metrics", None)
    if not callable(metrics_fn):
        return None
    metrics_obj = metrics_fn()
    try:
        return asdict(metrics_obj)
    except TypeError:
        return metrics_obj  # type: ignore[return-value]


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


def _run_solver_explain(solver_name: str, step_delay: float) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """Executa o solver no modo explicação, animando passo a passo."""
    registry = all_registered()
    solver_cls = registry[solver_name]
    solver = solver_cls()

    if not hasattr(solver, "solve_generator"):
        raise ValueError("Modo explicação requer solver com suporte a `solve_generator`.")

    board = st.session_state[KEY_BOARD].clone()
    board_placeholder = st.empty()
    status_placeholder = st.empty()

    solved_board: Optional[Any] = None

    for event in solver.solve_generator(board):
        if st.session_state.get(SOLVE_STOP, False):
            status_placeholder.warning("Execução interrompida pelo usuário.")
            break
        snapshot = event.board or board
        board = snapshot

        with board_placeholder.container():
            render_readonly_board(snapshot, highlight_cell=event.cell)

        status_text = f"{event.step_type.upper()} — célula {event.cell}, valor {event.value}"
        if event.reason:
            status_text += f" ({event.reason})"
        status_placeholder.info(status_text)

        time.sleep(max(step_delay, 0.01))

        if event.step_type == "finished":
            solved_board = snapshot

    metrics = _extract_metrics(solver)
    return solved_board, metrics


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
    if "backtracking" in solver_names:
        default_idx = solver_names.index("backtracking")
    elif st.session_state[SOLVE_SOLVER] in solver_names:
        default_idx = solver_names.index(st.session_state[SOLVE_SOLVER])

    solver_name = st.selectbox(
        "Escolha o algoritmo de resolução:",
        options=solver_names,
        index=default_idx,
        key=SOLVE_SOLVER,
    )

    explanation = SOLVER_EXPLANATIONS.get(solver_name, "Sem descrição disponível para este solver.")
    with st.container():
        st.info(explanation, icon="ℹ️")

    meta_cols = st.columns([2, 2, 2])
    meta_cols[0].metric("Dimensão", f"{board.size()}×{board.size()}")
    meta_cols[1].metric("ID", st.session_state[KEY_BOARD_ID] or "—")
    meta_cols[2].metric("Fonte", st.session_state[KEY_BOARD_SOURCE] or "—")

    explain_mode = st.checkbox("Modo explicação (visualizar passos)")
    step_delay = 0.15
    if explain_mode:
        step_delay = st.slider("Intervalo entre passos (s)", 0.05, 0.5, 0.15, 0.05)

    action_cols = st.columns([1, 1, 1])
    run_label = "Executar (Explain Mode)" if explain_mode else "Resolver"
    run_clicked = action_cols[0].button(run_label, type="primary")
    stop_clicked = action_cols[1].button("Parar", type="secondary")
    clear_clicked = action_cols[2].button("Limpar resultado", type="secondary")

    if clear_clicked:
        _clear_solver_result()

    if stop_clicked:
        st.session_state[SOLVE_STOP] = True

    if run_clicked:
        _clear_solver_result()  # limpa antes de nova execução
        st.session_state[SOLVE_STOP] = False
        solver_name = st.session_state[SOLVE_SOLVER] or solver_names[0]

        try:
            with st.spinner(f"Executando solver '{solver_name}'..."):
                if explain_mode:
                    solved_board, metrics = _run_solver_explain(solver_name, step_delay)
                else:
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

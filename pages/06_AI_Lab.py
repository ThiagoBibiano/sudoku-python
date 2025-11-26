"""Página do laboratório de IA (visualização e dicas do agente RL)."""

from __future__ import annotations

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from pathlib import Path

from core.board import Board
from core.rules import SudokuRules
from solvers.rl.inference import get_ai_hint, get_ai_probabilities, load_ai_model
from ui.components.board_view import render_readonly_board
from ui.state import KEY_BOARD, ensure_session_defaults
try:
    from sb3_contrib.ppo_mask import MaskablePPO
    from sb3_contrib.common.wrappers import ActionMasker
    from stable_baselines3.common.vec_env import DummyVecEnv
    from solvers.rl.env import FlattenSudokuActionSpace, SudokuGymEnv, sudoku_action_mask
except Exception:  # sb3 pode não estar instalado
    MaskablePPO = None  # type: ignore[assignment]


# Configuração da página e defaults de sessão
st.set_page_config(page_title="AI Lab", page_icon="🤖")
ensure_session_defaults()


@st.cache_resource
def get_model(path: str):
    """Carrega o modelo em cache para não recarregar a cada clique."""
    try:
        # Ajuste dropout=0.0 para inferência determinística
        return load_ai_model(path, device="cpu", dropout_rate=0.0)
    except Exception as exc:  # noqa: BLE001 - mostrar erro direto na UI
        st.error(f"Erro ao carregar modelo: {exc}")
        return None


@st.cache_resource
def load_rl_checkpoint(path: str):
    if MaskablePPO is None:
        st.error("sb3-contrib não está instalado; instale para usar o modelo RL.")
        return None
    try:
        return MaskablePPO.load(path, device="cpu")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro ao carregar checkpoint RL: {exc}")
        return None


def list_rl_checkpoints() -> list[str]:
    checkpoints: list[str] = []
    runs_dir = Path("runs/ppo_masked")
    if runs_dir.exists():
        checkpoints = sorted(
            str(p) for p in runs_dir.glob("model_*.zip") if p.is_file()
        )
    return checkpoints


def predict_with_rl(board: Board, model) -> tuple[int, int, int]:
    """Usa MaskablePPO para sugerir uma ação com máscara."""
    if MaskablePPO is None or model is None:
        return -1, -1, -1
    def _init():
        env = SudokuGymEnv(board.clone(), max_steps=500)
        env = FlattenSudokuActionSpace(env)
        return ActionMasker(env, sudoku_action_mask)
    vec_env = DummyVecEnv([_init])
    obs = vec_env.reset()
    action_masks = vec_env.env_method("action_mask")[0].reshape(-1)
    action, _ = model.predict(obs, action_masks=action_masks, deterministic=True)
    # Converte ação discreta de volta para (r,c,v)
    flat_env = vec_env.envs[0].env  # FlattenSudokuActionSpace
    r, c, v_idx = flat_env.action(int(action))
    return r, c, v_idx + 1


def solve_with_rl(board: Board, model, max_steps: int = 200) -> tuple[Board | None, int]:
    """Aplica ações RL iterativamente até resolver ou travar."""
    rules = SudokuRules()
    current = board.clone()
    for step in range(max_steps):
        if rules.is_solved(current):
            return current, step
        r, c, v = predict_with_rl(current, model)
        if r == -1:
            return None, step
        try:
            current = current.with_value(r, c, v)
        except Exception:
            return None, step
    return None, max_steps


def main() -> None:
    """Renderiza o laboratório de IA."""
    st.title("🤖 AI Lab (Laboratório de IA)")

    # 1. Verifica se há tabuleiro carregado
    if st.session_state[KEY_BOARD] is None:
        st.warning("Nenhum puzzle carregado. Vá para a página 'Load' primeiro.")
        if st.button("Ir para Load"):
            st.switch_page("pages/02_Load.py")
        return

    board: Board = st.session_state[KEY_BOARD]

    # 2. Seletor de Modelo / Pesos
    model_path = "policy_pretrain.pth"  # Padrão

    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        mode = st.radio(
            "Modo de Operação",
            ["Análise de Probabilidades", "Assistente de Jogo"],
            horizontal=True,
        )
    with col_cfg2:
        model_type = st.radio(
            "Modelo",
            ["Supervisionado", "RL (MaskablePPO)"],
            horizontal=True,
        )

    rl_checkpoints = list_rl_checkpoints() if model_type == "RL (MaskablePPO)" else []

    rl_model = None
    if model_type == "Supervisionado":
        model = get_model(model_path)
        if not model:
            st.error("Modelo supervisionado não encontrado. Treine primeiro (`python -m solvers.rl.trainer`).")
            return
    else:
        if not rl_checkpoints:
            st.warning("Nenhum checkpoint RL encontrado em runs/ppo_masked/model_*.zip.")
            return
        sel_ckpt = st.selectbox("Checkpoint RL", rl_checkpoints, index=len(rl_checkpoints) - 1)
        rl_model = load_rl_checkpoint(sel_ckpt)
        if rl_model is None:
            return

    # 3. Layout Principal
    col_board, col_info = st.columns([1, 1])

    with col_board:
        st.subheader("Tabuleiro Atual")
        # Renderiza tabuleiro estático (apenas leitura para o Lab)
        render_readonly_board(board)

    # 4. Lógica da IA
    with col_info:
        # Obter probabilidades da rede neural (9x9x9) apenas para o modelo supervisionado
        probs_grid = get_ai_probabilities(board, model) if model_type == "Supervisionado" else None

        if mode == "Análise de Probabilidades":
            if model_type != "Supervisionado":
                st.info("A visualização de probabilidades usa o modelo supervisionado. Selecione 'Supervisionado' acima.")
                return
            st.subheader("🧠 O que a IA está pensando?")

            # Seletores de coordenadas para "sondar" o cérebro da IA
            sel_col1, sel_col2 = st.columns(2)
            with sel_col1:
                r = st.number_input("Linha (0-8)", 0, 8, 0)
            with sel_col2:
                c = st.number_input("Coluna (0-8)", 0, 8, 0)

            cell_value = board.get(r, c)

            if cell_value != 0:
                st.info(f"A célula ({r}, {c}) já está preenchida com **{cell_value}**.")
                st.caption("Mesmo assim, a IA atribui estas probabilidades se estivesse vazia:")

            # Extrai probabilidades da célula (vetor de 9 posições)
            cell_probs = probs_grid[r, c]

            # Cria DataFrame para o gráfico
            df_probs = pd.DataFrame({"Dígito": list(range(1, 10)), "Confiança": cell_probs})

            # Gráfico de Barras com Altair
            chart = (
                alt.Chart(df_probs)
                .mark_bar()
                .encode(
                    x=alt.X("Dígito:O", title="Número"),
                    y=alt.Y("Confiança:Q", title="Probabilidade", scale=alt.Scale(domain=[0, 1])),
                    color=alt.condition(
                        alt.datum.Confiança > 0.5,
                        alt.value("green"),  # Destaque se muito confiante
                        alt.value("steelblue"),
                    ),
                    tooltip=["Dígito", alt.Tooltip("Confiança", format=".2%")],
                )
                .properties(height=300)
            )

            st.altair_chart(chart, use_container_width=True)

            top_guess = int(np.argmax(cell_probs)) + 1
            conf = float(np.max(cell_probs))
            st.write(f"💡 Melhor aposta da IA: **{top_guess}** ({conf:.1%} de certeza)")

        elif mode == "Assistente de Jogo":
            st.subheader("✨ Dica Inteligente")
            st.write("A IA analisará todo o tabuleiro e sugerirá a jogada mais segura.")

            if st.button("Pedir Dica"):
                if model_type == "Supervisionado":
                    hr, hc, hval = get_ai_hint(board, model)
                    confidence = probs_grid[hr, hc, hval - 1] if hr != -1 and probs_grid is not None else 0.0
                else:
                    hr, hc, hval = predict_with_rl(board, rl_model)
                    confidence = 0.0  # não calculamos prob explícita para RL

                if hr == -1:
                    st.error("A IA não encontrou movimentos válidos (ou o tabuleiro está cheio/travado).")
                else:
                    # Mostra a dica
                    st.success(f"A IA sugere colocar **{hval}** na Linha **{hr}**, Coluna **{hc}**.")
                    if model_type == "Supervisionado":
                        st.metric("Confiança da Rede", f"{confidence:.1%}")
                    else:
                        st.caption("Dica produzida pelo modelo RL (MaskablePPO).")

                    # Opção de aplicar
                    if st.button("Aplicar Dica"):
                        # Atualiza o estado
                        new_board = board.with_value(hr, hc, hval)
                        st.session_state[KEY_BOARD] = new_board
                        st.rerun()

            if model_type == "RL (MaskablePPO)":
                st.divider()
                st.subheader("🧩 Resolver com RL (iterativo)")
                st.caption("Aplica o agente RL passo a passo até resolver ou travar.")
                if st.button("Resolver agora"):
                    solved_board, steps = solve_with_rl(board, rl_model, max_steps=200)
                    if solved_board is None:
                        st.error(f"O agente RL não conseguiu concluir o puzzle em {steps} passos.")
                    else:
                        st.success(f"Puzzle resolvido pelo RL em {steps} passos.")
                        st.session_state[KEY_BOARD] = solved_board
                        st.rerun()


if __name__ == "__main__":
    main()

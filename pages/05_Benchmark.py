"""Página de benchmarks para comparar solvers em lote (Altair + drill-down)."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import altair as alt
import pandas as pd
import streamlit as st

from core.benchmark import BenchmarkSession
from core.io import PuzzleEntry, parse_ndjson
from ui.components.board_view import render_readonly_board
from solvers.registry import all_registered


# Chaves de session_state para preservar resultados/seleções
KEY_RESULTS = "benchmark_results_df"
KEY_ENTRY_MAP = "benchmark_entry_map"
KEY_STATUS_FILTER = "benchmark_status_filter"
KEY_PUZZLE_FILTER = "benchmark_puzzle_filter"
KEY_LOG_TIME = "benchmark_log_time"
KEY_LOG_NODES = "benchmark_log_nodes"
KEY_SOLVERS_SELECTED = "benchmark_solvers_selected"
KEY_DIFFICULTY = "benchmark_difficulty"


def _ensure_session_defaults() -> None:
    ss = st.session_state
    ss.setdefault(KEY_RESULTS, None)
    ss.setdefault(KEY_ENTRY_MAP, {})
    ss.setdefault(KEY_STATUS_FILTER, None)
    ss.setdefault(KEY_PUZZLE_FILTER, None)
    ss.setdefault(KEY_LOG_TIME, False)
    ss.setdefault(KEY_LOG_NODES, False)
    ss.setdefault(KEY_SOLVERS_SELECTED, None)
    ss.setdefault(KEY_DIFFICULTY, None)


def _load_ndjson(path: Path) -> List[PuzzleEntry]:
    if not path.exists():
        st.error(f"Arquivo não encontrado: {path}")
        return []
    text = path.read_text(encoding="utf-8")
    return parse_ndjson(text)


def _build_kpis(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Nenhum resultado para exibir.")
        return

    kpi_cols = st.columns(3)
    mean_time = df.groupby("Solver")["Time (s)"].mean().min()
    kpi_cols[0].metric("Menor tempo médio (s)", f"{mean_time:.3f}")

    mean_nodes = df.groupby("Solver")["Nodes"].mean(numeric_only=True).min()
    kpi_cols[1].metric("Menor média de nós", f"{mean_nodes:.0f}" if pd.notna(mean_nodes) else "—")

    success_rate = (df["Status"] == "ok").mean() * 100
    kpi_cols[2].metric("Taxa de sucesso (%)", f"{success_rate:.1f}%")


def _speedup(df: pd.DataFrame) -> None:
    solvers = df["Solver"].unique()
    if len(solvers) != 2:
        return
    pivot = df[df["Status"] == "ok"].groupby("Solver")["Time (s)"].mean()
    if len(pivot) == 2 and pivot.min() > 0:
        fastest = pivot.idxmin()
        slowest = pivot.idxmax()
        speedup = pivot[slowest] / pivot[fastest]
        st.info(f"Speedup: `{fastest}` está aproximadamente **{speedup:.1f}×** mais rápido que `{slowest}` na média.")


def _time_chart(df: pd.DataFrame, log_scale: bool) -> alt.Chart:
    scale = alt.Scale(type="log") if log_scale else alt.Scale(type="linear")
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Puzzle ID:N", sort=None),
            y=alt.Y("Time (s):Q", scale=scale),
            color="Solver:N",
            tooltip=["Puzzle ID", "Solver", alt.Tooltip("Time (s):Q", format=".3f"), "Nodes", "Status"],
        )
    )


def _nodes_chart(df: pd.DataFrame, log_scale: bool) -> alt.Chart:
    if not df["Nodes"].notna().any():
        return None
    scale = alt.Scale(type="log") if log_scale else alt.Scale(type="linear")
    return (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Puzzle ID:N", sort=None),
            y=alt.Y("Nodes:Q", scale=scale),
            color="Solver:N",
            tooltip=["Puzzle ID", "Solver", "Nodes", alt.Tooltip("Time (s):Q", format=".3f"), "Status"],
        )
    )


def _boxplot(df: pd.DataFrame, log_scale: bool) -> alt.Chart:
    scale = alt.Scale(type="log") if log_scale else alt.Scale(type="linear")
    return (
        alt.Chart(df)
        .mark_boxplot()
        .encode(
            x="Solver:N",
            y=alt.Y("Time (s):Q", scale=scale),
            color="Solver:N",
            tooltip=["Solver", alt.Tooltip("Time (s):Q", format=".3f")],
        )
    )


def _scatter(df: pd.DataFrame, log_time: bool, log_nodes: bool) -> Optional[alt.Chart]:
    data = df.dropna(subset=["Nodes"]).copy()
    if data.empty:
        return None
    x_scale = alt.Scale(type="log") if log_nodes else alt.Scale(type="linear")
    y_scale = alt.Scale(type="log") if log_time else alt.Scale(type="linear")
    return (
        alt.Chart(data)
        .mark_circle(size=80, opacity=0.7)
        .encode(
            x=alt.X("Nodes:Q", scale=x_scale),
            y=alt.Y("Time (s):Q", scale=y_scale),
            color="Solver:N",
            tooltip=["Puzzle ID", "Solver", "Nodes", alt.Tooltip("Time (s):Q", format=".3f"), "Status"],
        )
    )


def _drill_down(df: pd.DataFrame, entry_map: Dict[str, PuzzleEntry]) -> None:
    if df.empty:
        return
    st.subheader("Drill-down do puzzle")

    filtered_ids = df["Puzzle ID"].unique().tolist()
    selected_id = st.selectbox("Escolha um Puzzle ID para inspecionar", options=filtered_ids, index=0)
    entry = entry_map.get(selected_id)
    if entry is None:
        st.warning("Puzzle não encontrado no lote carregado.")
        return
    st.caption(f"Puzzle `{selected_id}` — status: {df[df['Puzzle ID']==selected_id]['Status'].iloc[0]}")
    render_readonly_board(entry.board)


def main() -> None:
    st.set_page_config(page_title="Benchmark Lab", page_icon="📊", layout="wide")
    _ensure_session_defaults()
    st.title("📊 Benchmark Lab")
    st.write("Compare solvers em lote de puzzles (NDJSON) e visualize métricas.")

    data_dir = Path("data/puzzles")
    difficulties = ["easy.ndjson", "hard.ndjson"]
    available = [d for d in difficulties if (data_dir / d).exists()]
    if not available:
        st.error("Nenhum arquivo NDJSON encontrado em data/puzzles.")
        return

    st.sidebar.header("Configuração")
    diff_index = 0
    if st.session_state[KEY_DIFFICULTY] in available:
        diff_index = available.index(st.session_state[KEY_DIFFICULTY])
    difficulty = st.sidebar.selectbox("Dificuldade", options=available, index=diff_index)
    st.session_state[KEY_DIFFICULTY] = difficulty

    registry = all_registered()
    solver_options = sorted(registry.keys())
    default_solvers = st.session_state[KEY_SOLVERS_SELECTED] or [
        s for s in ["forward_checking", "heuristic_backtracking"] if s in solver_options
    ]
    selected_solvers = st.sidebar.multiselect(
        "Solvers a comparar",
        options=solver_options,
        default=default_solvers,
    )
    st.session_state[KEY_SOLVERS_SELECTED] = selected_solvers
    sample_size = st.sidebar.slider("Quantidade de puzzles", min_value=1, max_value=100, value=10, step=1)
    timeout = st.sidebar.slider("Timeout por puzzle (s)", min_value=1, max_value=60, value=10, step=1)

    run = st.button("Executar Benchmark", type="primary", width="stretch")

    if run:
        if not selected_solvers:
            st.warning("Selecione ao menos um solver.")
            return

        entries = _load_ndjson(data_dir / difficulty)
        if not entries:
            st.warning("Nenhum puzzle carregado.")
            return

        entries = entries[:sample_size]
        entry_map = {e.id: e for e in entries}
        session = BenchmarkSession(timeout=timeout)

        progress = st.progress(0.0)
        total = len(selected_solvers) * len(entries)
        done = 0
        res_frames: List[pd.DataFrame] = []

        for solver_name in selected_solvers:
            df = session.run([solver_name], entries)
            res_frames.append(df)
            done += len(entries)
            progress.progress(done / total)

        progress.empty()
        results_df = pd.concat(res_frames, ignore_index=True)
        st.session_state[KEY_RESULTS] = results_df
        st.session_state[KEY_ENTRY_MAP] = entry_map
        st.session_state[KEY_STATUS_FILTER] = None
        st.session_state[KEY_PUZZLE_FILTER] = None

    results_df = st.session_state[KEY_RESULTS]
    entry_map = st.session_state[KEY_ENTRY_MAP]

    if results_df is None or results_df.empty:
        st.info("Nenhum benchmark executado ainda.")
        return

    st.subheader("KPIs")
    _build_kpis(results_df)
    _speedup(results_df)

    st.divider()
    st.subheader("Filtros")
    status_options = sorted(results_df["Status"].unique().tolist())
    default_status = st.session_state[KEY_STATUS_FILTER] or status_options
    default_status = [s for s in default_status if s in status_options] or status_options
    selected_status = st.multiselect("Filtrar status", options=status_options, default=default_status)
    st.session_state[KEY_STATUS_FILTER] = selected_status

    puzzle_options = sorted(results_df["Puzzle ID"].unique().tolist())
    default_puzzles = st.session_state[KEY_PUZZLE_FILTER] or puzzle_options
    default_puzzles = [p for p in default_puzzles if p in puzzle_options] or puzzle_options
    selected_puzzles = st.multiselect("Filtrar Puzzle ID", options=puzzle_options, default=default_puzzles)
    st.session_state[KEY_PUZZLE_FILTER] = selected_puzzles

    filtered = results_df[
        results_df["Status"].isin(selected_status) & results_df["Puzzle ID"].isin(selected_puzzles)
    ]

    st.subheader("Gráficos")
    col_scale = st.columns(3)
    log_time = col_scale[0].checkbox("Tempo em escala log", value=st.session_state[KEY_LOG_TIME], key=KEY_LOG_TIME)
    log_nodes = col_scale[1].checkbox("Nós em escala log", value=st.session_state[KEY_LOG_NODES], key=KEY_LOG_NODES)

    time_chart = _time_chart(filtered, log_time)
    nodes_chart = _nodes_chart(filtered, log_nodes)
    box_chart = _boxplot(filtered, log_time)
    scatter_chart = _scatter(filtered, log_time, log_nodes)

    st.altair_chart(time_chart, width="stretch")
    if nodes_chart is not None:
        st.altair_chart(nodes_chart, width="stretch")

    st.subheader("Distribuição de tempo por solver")
    st.altair_chart(box_chart, width="stretch")

    if scatter_chart is not None:
        st.subheader("Correlação Tempo x Nós")
        st.altair_chart(scatter_chart, width="stretch")

    _drill_down(filtered, entry_map)

    st.subheader("Resultados detalhados")
    st.dataframe(filtered, width="stretch")


if __name__ == "__main__":
    main()

"""Página 'Sobre' (About)."""

from __future__ import annotations

import streamlit as st


def main() -> None:
    """Renderiza a página About."""
    st.title("ℹ️ Sobre")
    st.write(
        """
        **Sudokku** é um projeto modular para Sudoku em Python, focado em:
        - Núcleo limpo (`Board`) e validação (`SudokuRules`);
        - IO robusto (TXT, JSON, **NDJSON por dificuldade**);
        - UI fina em Streamlit (MVP);
        - Futuras integrações com solvers (backtracking, DLX/CP-SAT, metaheurística, NN).

        **Arquitetura**: SRP/SOLID, docstrings Google, PEP8, OOP.
        """
    )

    st.subheader("Roadmap (resumo)")
    st.markdown(
        "- ✅ Etapa 0–4: Base, Core, Regras, IO\n"
        "- 🚧 Etapa 5: Streamlit MVP (esta)\n"
        "- 🔜 Etapas 6–14: Solvers, Explain, Propagação, Benchmarks e AI Lab\n"
    )

    st.caption("Execução: `streamlit run sudokku/ui/app.py`")


if __name__ == "__main__":
    main()

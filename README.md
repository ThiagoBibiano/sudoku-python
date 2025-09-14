# Sudokku

Aplicação em Python para manipulação e resolução de Sudoku, seguindo princípios **SOLID**, **PEP8** e **Orientação a Objetos**.  
O projeto terá integração com **Streamlit** para visualização, e futuramente com **solvers baseados em IA** (otimizadores discretos, meta-heurísticas e redes neurais).

## Objetivos
- Engine central para Sudoku (representação, validação e IO).
- Solvers clássicos (backtracking, DLX, CP-SAT).
- Extensibilidade para heurísticas e IA.
- Interface em Streamlit (jogar, resolver, comparar, treinar).
- Benchmark de diferentes abordagens.

## Estrutura inicial
```
sudokku/
core/
solvers/
ui/
utils/
data/
tests/
docs/
```

## Como contribuir
- Branch principal de desenvolvimento: `developer`
- Use branches no formato `feature/...`, `fix/...`, `docs/...`.
- Commits seguem o padrão: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`.

---


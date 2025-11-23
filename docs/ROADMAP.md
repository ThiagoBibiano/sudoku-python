# Roadmap de Desenvolvimento

## Etapas
- [x] Etapa 0 — Base do repositório
- [x] Etapa 1 — Estrutura de pastas + contratos (sem lógica ainda)
- [x] Etapa 2 — Core mínimo: tipos e Board
- [x] Etapa 3 — Validador de regras
- [x] Etapa 4 — IO simples
- [x] Etapa 5 — Streamlit MVP (esqueleto multipáginas)
- [x] Etapa 6 — Solver base + backtracking
- [x] Etapa 7 — Integração Streamlit
- [x] Etapa 8 — Explain Mode + MRV/LCV
- [x] Etapa 9 — Propagação de candidatos
- [x] Etapa 10 — Benchmark page
- [x] Etapa 11 — Solver discreto (DLX ou CP-SAT)
- [x] Etapa 12 — Metaheurística
- [x] Etapa 13 — AI Lab
- [ ] Etapa 14 — Polimento v0.1

## Detalhamento da Etapa 13 — AI Lab (RL + Imitation Learning)

- Objetivo: treinar um agente autônomo que olha o tabuleiro e sugere o dígito mais provável (99% de confiança para um “5” em determinada célula).
- Estrutura nova (já iniciada): `solvers/rl/` com `env.py` (SudokuGymEnv + RewardConfig) e stubs para `agent.py`, `trainer.py` e `wrapper.py`.
- Ambiente Gymnasium:
  - Observação: tensor one-hot `(size, size, size+1)` com canal extra para pistas iniciais.
  - Ação: `MultiDiscrete([size, size, size])` representando `(linha, coluna, valor-1)`.
  - Máscara de ação: gerada a partir de `SudokuRules.can_place` para evitar jogadas ilegais.
  - Recompensa sugerida: +0.1 jogada válida; +1 linha/coluna/box completos; +10 puzzle resolvido; -0.5 inválida; -0.01 por passo.
- Pipeline de dados e imitation learning (9M puzzles):
  - Converter dataset em tensores PyTorch via DataLoader streaming (evitar carregar tudo em RAM).
  - Fase 1: behavior cloning supervisionado com loss de entropia cruzada → salva `policy_pretrain.pth`.
  - Fase 2: fine-tuning em RL (ex.: PPO/MaskablePPO) carregando pesos pré-treinados para cobrir casos “hard”.
- Tecnologias sugeridas (opcional no requirements): `gymnasium`, `stable-baselines3`, `sb3-contrib` (MaskablePPO) e `torch`.
- Experimentos propostos:
  - E1: Criar e testar o ambiente (`solvers/rl/env.py`) com loop aleatório.
  - E2: Pipeline de dados em lotes para os 9M puzzles.
  - E3: Treino supervisionado + solver neural para benchmark.
  - E4: Agente RL com máscara de ação treinado por ~1M timesteps.
- UI (nova página `06_AI_Lab.py`): seletor entre modelo supervisionado e RL, gráfico de probabilidades por célula, botão “Dica da IA” preenchendo a célula mais confiável.
- Métricas-chave: % de ações válidas (ideal 100% com máscara), taxa de solução em puzzles “Expert” e latência de inferência (<50ms em CPU).
- Próximo passo: finalizar integração do `SudokuGymEnv` com o pipeline de treino e adicionar o solver neural (wrapper) para uso no app.

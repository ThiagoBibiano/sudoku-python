# Algoritmos de Resolução (visão técnica)

A aplicação trata o Sudoku como um **Problema de Satisfação de Restrições (CSP)**:
cada célula é uma variável, o domínio vai de 1 a 9 e as restrições são linha/coluna/subgrade.

Hoje o projeto explora quatro famílias de abordagem:

1. **Backtracking clássico** (com heurísticas MRV/LCV).
2. **DLX (Algorithm X / Dancing Links)** — exato via *exact cover*.
3. **CP-SAT** — modelagem declarativa em programação por restrições.
4. **Meta-heurísticas** — heurísticas de otimização, começando por Simulated Annealing.

A ideia é ser um laboratório didático: mesmas instâncias, algoritmos diferentes.

---

## 1. Backtracking “puro” (força bruta com retrocesso)

- **Ideia:** Explora o tabuleiro como um labirinto de decisões.
  - Escolhe uma célula vazia.
  - Tenta valores de 1 a 9 que não quebrem as regras.
  - Avança recursivamente.
  - Se travar (nenhum valor possível), volta (“backtrack”) para a decisão anterior.

- **Passos básicos do algoritmo:**
  1. Encontrar uma célula vazia.
  2. Gerar a lista de candidatos válidos usando as restrições de linha, coluna e box 3x3.
  3. Para cada candidato:
     - Atribuir o valor.
     - Chamar recursivamente o solver.
     - Se a chamada recursiva resolver o tabuleiro, retornar sucesso.
     - Caso contrário, desfazer a jogada e tentar o próximo valor.
  4. Se nenhum candidato funcionar, sinalizar falha para forçar o backtrack.

- **Propriedades:**
  - **Completo:** encontra solução se existir.
  - **Potencialmente lento** para Sudokus difíceis sem heurísticas.

---

## 2. Heurísticas sobre o backtracking (MRV e LCV)

As heurísticas não mudam o que é solução, apenas **como** a árvore de busca é explorada.

### 2.1 MRV (Minimum Remaining Values) — “falhar primeiro”

- **O que faz:**
  Escolhe sempre a célula vazia com **menos candidatos válidos**.

- **Motivação:**
  - Atacar cedo os **gargalos** do problema.
  - Se uma célula tiver 0 candidatos, a ramificação morre rápido.
  - Se tiver 1 candidato, a decisão é praticamente forçada.

- **Efeito:**
  - Reduz o tamanho efetivo da árvore de busca.
  - Diminui o número de chamadas recursivas em muitos casos.

- **No projeto:**
  MRV é a estratégia de **escolha de variável**:
  > próxima variável = célula vazia com menor número de candidatos.

---

### 2.2 LCV (Least Constraining Value) — “deixar portas abertas”

Se MRV escolhe **qual célula** decidir, LCV define **em que ordem testar os valores** dessa célula.

- **O que faz:**
  Ordena os candidatos para uma célula de modo que o solver teste primeiro
  o valor que **menos restringe** os vizinhos (linha, coluna e box).

- **Motivação:**
  - Evitar decisões que “estrangulem” o resto do tabuleiro, eliminando muitos candidatos de outras células.

- **Como funciona (conceitualmente):**
  1. Para cada candidato `v`:
     - Estima o impacto de colocar `v` na célula (quantos candidatos some dos vizinhos).
  2. Ordena os candidatos do menor impacto para o maior.
  3. O backtracking segue essa ordem “mais amigável”.

- **Efeito:**
  - Não altera o conjunto de soluções, apenas a **ordem de exploração**.
  - Em média, reduz a quantidade de backtracking.

- **No projeto:**
  LCV é a estratégia de **ordenar os valores**:
  > MRV escolhe a célula, LCV define a ordem dos candidatos.

---

## 3. Combinação: Backtracking + MRV + LCV

Na prática, o solver baseado em backtracking funciona assim:

1. **Escolha da variável:** MRV
2. **Escolha da ordem dos valores:** LCV
3. **Mecanismo de busca:** backtracking recursivo clássico.

Isso mantém a **correção** do backtracking (se existe solução, ela será encontrada) e permite estudar:

- Impacto de heurísticas de **escolha de variável**.
- Impacto de heurísticas de **ordenação de valores**.
- Diferenças de desempenho para o mesmo conjunto de instâncias.

---

## 4. DLX (Algorithm X com Dancing Links)

DLX é uma implementação eficiente do **Algorithm X**, proposto por Donald Knuth,
para resolver problemas de **exact cover**.

### 4.1 Sudoku como *exact cover*

A ideia é mapear o Sudoku para uma matriz binária onde:

- Cada **linha** da matriz representa uma possível colocação `(linha, coluna, valor)`.
- Cada **coluna** representa uma restrição que deve ser satisfeita exatamente uma vez.

Típicas colunas de restrição para Sudoku:

1. **Célula ocupada:**
   Cada célula (linha, coluna) deve receber exatamente um valor.
2. **Linha–valor:**
   Para cada linha e cada dígito, aquele dígito aparece exatamente uma vez na linha.
3. **Coluna–valor:**
   Idem para colunas.
4. **Box–valor (subgrade 3x3):**
   Cada dígito aparece exatamente uma vez em cada subgrade.

Uma solução do Sudoku corresponde a um **conjunto de linhas** da matriz
que cobre todas as colunas (todas as restrições) **uma única vez**.

### 4.2 Algorithm X + Dancing Links

- **Algorithm X:**
  É um algoritmo de backtracking genérico sobre a matriz de exact cover.
- **Dancing Links (DLX):**
  É uma estrutura de dados baseada em listas duplamente ligadas que permite:
  - “Cobrir” e “descobrir” colunas/linhas de forma muito eficiente.
  - Reverter operações de forma barata na recursão.

### 4.3 Propriedades no contexto do projeto

- **Exato:** assim como o backtracking, encontra soluções corretas.
- **Geral:** o motor DLX não “sabe” nada de Sudoku; recebe só a matriz de exato cover.
- **Didático:**
  - Mostra como problemas de puzzle podem ser transformados em outra classe de problema (exact cover).
  - Permite comparar:
    - backtracking diretamente no tabuleiro
    - vs backtracking sobre a representação matricial (DLX).

---

## 5. CP-SAT (Programação por Restrições + SAT)

CP-SAT é uma abordagem onde o Sudoku é modelado como um **modelo matemático declarativo**
e entregue a um solver de **programação por restrições/inteiros**.

### 5.1 Modelagem típica para Sudoku

- **Variáveis:**
  - `x[r, c] ∈ {1..9}` para cada linha `r` e coluna `c`.

- **Restrições:**
  1. **Respeitar as pistas:**
     - Se a entrada já tem um valor em `(r, c)`, então `x[r, c]` é fixado nesse valor.
  2. **Linhas:**
     - Todos os valores de uma linha são diferentes (`AllDifferent`).
  3. **Colunas:**
     - Todos os valores de uma coluna são diferentes.
  4. **Subgrades 3x3:**
     - Todos os valores de cada bloco 3x3 são diferentes.

Opcionalmente, é possível adicionar:

- Restrições extras (por exemplo, garantir unicidade de solução).
- Critérios de otimização (não usual para Sudoku, mas possível).

### 5.2 Como o solver CP-SAT trabalha (visão de alto nível)

- Traduz o modelo em uma combinação de:
  - **Cláusulas SAT**,
  - **Restrições inteiras**,
  - Técnicas de propagação e *branch-and-bound*.
- A partir daí, o solver executa:
  - Propagação de restrições,
  - Decisões sobre variáveis,
  - Backtracking guiado por heurísticas internas.

### 5.3 Propriedades no contexto do projeto

- Você **não implementa o algoritmo de busca na mão**: só **declara o modelo**.
- O mesmo solver CP-SAT serviria para:
  - Sudoku,
  - Escalonamento,
  - Alocação de recursos,
  - etc.
- Didaticamente, permite comparar:
  - **Abordagem “algorítmica” manual** (backtracking, DLX)
  - vs **abordagem “modelagem + solver genérico”** (CP-SAT).

---

## 6. Meta-heurísticas

Meta-heurísticas tratam o Sudoku como **otimização** em vez de busca exata. A estratégia adotada aqui é didática e reaproveita infraestrutura comum:

- **Representação:**
  - As pistas são fixadas e imutáveis.
  - Cada linha é preenchida com uma permutação aleatória dos números faltantes, garantindo que as linhas sempre contenham 1..9.

- **Função de custo:**
  - Penaliza duplicatas em **colunas** e em **subgrades 3x3**.
  - `cost = 0` significa solução válida; o histórico de custo é armazenado para visualização.

- **Operador de vizinhança:**
  - Escolhe uma linha aleatória, seleciona duas posições **não fixas** e troca os valores, preservando as pistas originais.

### 6.1 Simulated Annealing (SA)

- **Ideia:** busca local que aceita piores soluções com probabilidade proporcional à temperatura, permitindo escapar de mínimos locais.
- **Parâmetros principais:** temperatura inicial `T0`, taxa de resfriamento `alpha`, `max_iters` e semente para reprodutibilidade.
- **Fluxo:**
  1. Gera uma solução inicial válida por linha.
  2. Gera um vizinho com o operador descrito acima.
  3. Calcula `Δ = cost(neighbor) - cost(current)`.
  4. Aceita melhorias (`Δ <= 0`) ou aceita piores soluções com `exp(-Δ / T)`.
  5. Atualiza a melhor solução e registra o histórico de custo.
  6. Reduz a temperatura `T *= alpha` a cada iteração.
- **No projeto:** implementado em `solvers/metaheuristics/sa.py`, utilizando helpers comuns em `solvers/metaheuristics/base_meta.py`.

### 6.2 Algoritmo Genético (AG)

- **Ideia:** população de tabuleiros completos, avaliados pela mesma função de custo; operadores de crossover/mutação preservam as pistas.
- **Parâmetros principais:** tamanho da população (`pop_size`), número de gerações (`n_generations`), probabilidade de crossover/mutação, tamanho do torneio e fração de elitismo.
- **Fluxo adotado:**
  1. Geração inicial: cada indivíduo é criado com a estratégia de permutações por linha.
  2. Avaliação: custo baseado em duplicatas de colunas/subgrades.
  3. Seleção: torneio com `k` indivíduos, escolhendo o de menor custo.
  4. Crossover: por linha, copiando valores não fixos de um dos pais (50/50) para o filho; as pistas são preservadas.
  5. Mutação: aplicação opcional do operador de vizinhança (troca em linha não fixa).
  6. Elitismo: fração do topo da população é copiada diretamente para a próxima geração.
- **No projeto:** implementado em `solvers/metaheuristics/ga.py`, reutilizando a base comum em `base_meta.py` e registrado para consumo no app.

**Notas práticas:**

- As seeds configuráveis na `MetaheuristicConfig` permitem repetir experimentos e comparar curvas de custo no Streamlit.
- A coleta de histórico (`cost_history`) guarda o melhor custo de cada geração para visualização e exportação.
- Parâmetros conservadores (ex.: `pop_size` menor com elitismo moderado) tendem a convergir mais rápido em cenários demonstrativos; valores maiores favorecem diversidade em estudos de comparação.

### 6.3 Próximos passos

- Experimentar outras meta-heurísticas (Tabu Search, VNS) usando a mesma base de custo/vizinhança.
- Expor hiperparâmetros e gráficos de custo no Streamlit para comparação com solvers exatos.

---

## 7. Comparando as abordagens

Resumo das abordagens principais:

| Abordagem         | Tipo              | Quem controla a busca?      | Vantagens didáticas                               |
|-------------------|-------------------|-----------------------------|---------------------------------------------------|
| Backtracking      | Exato, CSP direto | Código do projeto           | Simples, bom para ver recursão + heurísticas      |
| Backtracking+MRV/LCV | Exato, CSP direto | Código do projeto        | Mostra impacto de heurísticas de busca            |
| DLX (Algorithm X) | Exato, *exact cover* | Código do projeto        | Ilustra transformação para outra estrutura (matriz) |
| CP-SAT            | Exato (em tese)   | Solver de terceiros (CP-SAT)| Enfatiza modelagem e uso de solver genérico       |
| Simulated Annealing | Heurístico (otimização) | Código do projeto    | Visualiza curva de custo, aceita piores soluções no começo |
| Algoritmo Genético  | Heurístico (otimização) | Código do projeto    | Compara paradigmas populacionais (crossover/mutação) |


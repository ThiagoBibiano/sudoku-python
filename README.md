# Sudokku (sudoku-python)

Aplicação em Python para **manipulação, estudo e resolução de Sudoku**, seguindo princípios **SOLID**, **PEP8** e **orientação a objetos**.

O projeto serve tanto como **engine de Sudoku** quanto como um **playground de algoritmos** (solvers clássicos, técnicas de IA) com uma interface em **Streamlit** para visualização e experimentos.

> **Status do projeto:** em desenvolvimento 🚧

---

## 🧩 Objetivos do projeto

- ✅ Criar uma **engine central de Sudoku** (representação de tabuleiro, validação de movimentos, leitura/escrita de puzzles).
- ✅ Disponibilizar uma **interface web com Streamlit** para jogar e visualizar soluções.
- ✅ Implementar **solvers clássicos**:
  - Backtracking
  - DLX (Dancing Links)
  - Modelagem para solvers de Programação por Restrições / CP-SAT
- ✅ Permitir **extensibilidade para heurísticas e IA**:
  - Meta-heurísticas (ex.: Simulated Annealing e Algoritmo Genético)
  - Redes neurais / modelos de ML (a explorar)
- ⏳ Criar um **benchmark comparativo** entre diferentes abordagens de solução.

---

## 🗂 Estrutura do projeto

```text
sudoku-python/
├── app.py             # Entrypoint da aplicação Streamlit (multi-page app)
├── core/              # Modelos centrais (tabuleiro, célula, puzzle, validação)
├── solvers/           # Algoritmos de solução (clássicos e experimentais)
├── ui/                # Componentes de interface / helpers para Streamlit
├── pages/             # Páginas adicionais do app Streamlit (Home, Load, Play, etc.)
├── utils/             # Funções utilitárias (logs, helpers, etc.)
├── data/
│   └── puzzles/       # Conjunto de puzzles de exemplo (ex.: NDJSON)
├── tests/             # Testes automatizados
├── docs/              # Documentação complementar, notas de design, etc.
├── requirements.txt   # Dependências do projeto
├── CONTRIBUTING.md    # Guia de contribuição
└── README.md          # Este arquivo 🙂
````

A organização é pensada para facilitar a evolução do projeto, permitindo que **engine**, **solvers**, **UI** e **dados** evoluam de forma relativamente independente.

---

## ▶️ Como executar localmente

### 1. Clonar o repositório

```bash
git clone https://github.com/ThiagoBibiano/sudoku-python.git
cd sudoku-python
```

### 2. Criar e ativar um ambiente virtual (opcional, mas recomendado)

```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> Use a versão de Python 3.x que você preferir (idealmente a mesma usada no desenvolvimento).

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Rodar a aplicação Streamlit

```bash
streamlit run app.py
```

Isso deve abrir (ou instruir você a abrir) o app no navegador, normalmente em:

```text
http://localhost:8501
```

---

## 💡 O que o app faz hoje (visão geral)

O objetivo é que o app permita:

* Carregar puzzles a partir de arquivos em `data/puzzles/` (ex.: NDJSON).
* Definir um puzzle atual para ser jogado/visualizado.
* Mostrar o tabuleiro de Sudoku de forma amigável.
* Servir de base para:

  * Experimentar diferentes solvers (clássicos, DLX e meta-heurísticos);
  * Comparar tempo de solução, qualidade das abordagens e evolução de custo;
  * Criar interfaces de apoio ao estudo de algoritmos.

À medida que novas funcionalidades forem implementadas (solvers, heurísticas, IA etc.), elas serão expostas via UI do Streamlit.

---

## 🧪 Testes

Quando a suíte de testes estiver populada, a execução será algo como:

```bash
pytest
# ou
python -m pytest
```

A pasta `tests/` é o lugar para centralizar:

* Testes unitários dos modelos da pasta `core/`;
* Testes de integração dos solvers;
* Testes de utilitários e loaders de puzzles.

---

## 🛣 Roadmap (proposta)

Alguns passos planejados para o futuro do projeto:

* [x] Finalizar engine básica de Sudoku (linhas, colunas, subgrades, regras).
* [x] Implementar solver por **backtracking** com interface para comparação.
* [x] Implementar solver via **DLX (Dancing Links)**.
* [x] Integrar com algum solver de **CP-SAT / programação por restrições**.
* [x] Criar módulo de **benchmark**:

  * Coleção de puzzles de diferentes dificuldades;
  * Medição de tempo e número de iterações;
  * Relatórios simples (tabelas/gráficos).
* [x] Melhorar a interface Streamlit:

  * Escolha de puzzle por dificuldade/ID;
  * Highlight de conflitos/erros;
  * Modo “aprender” (mostrando o passo a passo do solver).
* [ ] Explorar abordagens de **IA / ML**:

  * Heurísticas de escolha de célula/valor;
  * Rede neural para sugerir jogadas ou inicializar soluções.

---

## ♨️ Meta-heurísticas

O projeto agora inclui uma camada para **solvers meta-heurísticos** com foco didático. Os principais pontos:

* **Infraestrutura comum**: `solvers/metaheuristics/base_meta.py` padroniza configuração, custo e coleta de histórico.
* **Simulated Annealing (SA)**: disponível em `solvers/metaheuristics/sa.py`, usa custo baseado em conflitos de colunas e subgrades.
* **Algoritmo Genético (AG)**: implementado em `solvers/metaheuristics/ga.py`, com crossover por linhas, mutação via troca e elitismo opcional.
* **Integração com Streamlit**: os meta-solvers seguem a interface geral de `solvers/`, permitindo seleção e visualização no app.
* **Testes**: a suíte `tests/test_metaheuristics.py` garante reprodutibilidade e rastreamento do histórico de custo.

### Como usar no Streamlit

1. Inicie o app com `streamlit run app.py` e acesse a página de solvers meta-heurísticos.
2. Escolha o solver desejado (SA ou GA) no seletor de solvers.
3. Ajuste hiperparâmetros via sliders:
   * **SA**: temperatura inicial (`T0`), `alpha`, número máximo de iterações.
   * **GA**: tamanho da população (`pop_size`), número de gerações (`n_generations`), probabilidade de crossover/mutação, tamanho do torneio e elitismo.
4. Execute o solver para visualizar o tabuleiro resultante e o **histórico de custo** por iteração/geração.

> Dica: defina uma **seed** na configuração do solver para repetir experimentos e comparar curvas de custo entre execuções.

---

## 🤝 Como contribuir

Contribuições são bem-vindas! ✨

* Branch principal de desenvolvimento: `developer`
* Crie branches no formato:

  * `feature/...`
  * `fix/...`
  * `docs/...`
* Use commits no padrão:

  * `feat: ...`
  * `fix: ...`
  * `docs: ...`
  * `refactor: ...`
  * `chore: ...`

Para mais detalhes (fluxo de contribuição, estilo de código, etc.), veja o arquivo **`CONTRIBUTING.md`**.

---

## 📬 Contato

Projeto mantido por **Thiago Bibiano**.
Para dúvidas, sugestões ou colaboração, entre em contato:

🔗 **LinkedIn:** https://www.linkedin.com/in/thiago-bibiano-da-silva-510b3b15b/

Sinta-se à vontade para abrir uma **issue** ou **pull request** no repositório!


```text
Divirta-se quebrando a cabeça com Sudoku… e com o código. 🙂
```

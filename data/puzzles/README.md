# Conjunto de Puzzles (Dados de Exemplo)

Esta pasta contém arquivos de puzzles de Sudoku para testes e benchmarks.

## Estrutura

- **Arquivos NDJSON (lote, 1 por dificuldade):**
  - `easy.ndjson`
  - `medium.ndjson`
  - `hard.ndjson`
  - `expert.ndjson`

Cada arquivo NDJSON contém **um puzzle por linha** (formato JSON **sem espaços extras**), com UTF-8 (sem BOM).

### Esquema NDJSON por linha

```json
{"id":"<string única no arquivo>","puzzle":"<string com 81 caracteres 1-9 ou .>","n":3}
```

* `id`: **obrigatório**, string única **dentro do arquivo**.
* `puzzle`: **obrigatório**, **81** caracteres (`1–9` e `.`). O ponto (`.`) representa célula vazia.
* `n`: **opcional**; se ausente, assume-se `3` (9×9).

  > Por ora, apenas `n=3` é suportado. Linhas com `n` diferente serão rejeitadas pela importação.

**Regras adicionais**

* Linhas vazias são ignoradas.
* Comentários **não** são permitidos.
* Codificação: **UTF-8**, sem BOM.

### Exemplos válidos (9×9)

```ndjson
{"id":"easy-0001","n":3,"puzzle":"3.6......85.9.3........1.6..........6.3..8....173.4..9.......3.4....6...5..81..9."}
{"id":"easy-0002","puzzle":".5.69......9...8.4821.5....76....1.8..4...79..........1..97..8..4.8..51...7...4.."}
```

> Observação: No segundo exemplo, `n` foi omitido e, portanto, será assumido como `3`.

---

## Outros formatos (unitários)

Além dos lotes NDJSON, o projeto também aceita **puzzles unitários** (um por arquivo/string), úteis em testes rápidos:

* **TXT (compacto)**: string única com `size^2` caracteres. Vazio pode ser `0` ou `.`.
* **TXT (grid)**: múltiplas linhas; no modo flex, espaços e separadores (`|`, `-`, `+`) são ignorados; `.` é vazio.
* **JSON (objeto)**: `{"grid": [[...], ...], "n": 3?}` — `n` é opcional e é inferido se ausente.

---

## Boas práticas

* Use IDs previsíveis: `<difficulty>-<sequencial>`, por exemplo `easy-0001`.
* Evite trailing spaces e linhas em branco entre objetos no NDJSON.
* Ao compartilhar arquivos, valide localmente com o módulo de IO do projeto (funções `load_ndjson` e `parse_ndjson`).


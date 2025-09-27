"""Rotinas de entrada/saída (IO) e parsing de puzzles de Sudoku.

Responsabilidade:
    Este módulo lida exclusivamente com conversões entre representações
    textuais (TXT/CSV/JSON/NDJSON) e o modelo interno (`Board`). Ele não
    aplica regras do Sudoku (essas ficam em `SudokuRules`) e não gerencia
    candidatos/propagação.

Formatos unitários (um tabuleiro):
    - TXT (compacto): string contínua com size^2 caracteres ("0" ou "." para vazio).
    - TXT (grid): linhas formatadas (ex.: 9 linhas de 9 colunas), "." para vazio.
    - JSON (objeto): {"grid": [[...]], "n": 3?} (n opcional; será inferido se ausente).

Formato em lote (múltiplos tabuleiros):
    - NDJSON (um JSON por linha), **um arquivo por dificuldade** (ex.: easy.ndjson):
        {"id": "easy-0001", "puzzle": "3.6......85.9.3........1.6..........6.3..8....173.4..9.......3.4....6...5..81..9."}
      Regras NDJSON (9x9):
        * 81 caracteres exatos
        * Apenas '1'..'9' e '.' (ponto) como vazio
        * `id` obrigatório (string) e **único dentro do arquivo**
        * Linhas vazias ignoradas; comentários não permitidos
        * Codificação UTF-8, sem BOM

Decisões:
    - Para formatos "unitários", suportamos `0` e/ou '.' como vazio.
    - Para NDJSON (lote), seguimos estritamente a especificação: **apenas '.'**
      representa vazio e apenas 9x9 (81 chars).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from .board import Board
from .types import Digit, Grid, Size, DEFAULT_N, EMPTY


# ============================================================================
# Modelos e utilitários
# ============================================================================

@dataclass(frozen=True)
class PuzzleEntry:
    """Registro de puzzle importado/exportado em lote (NDJSON).

    Attributes:
        id: Identificador único dentro do arquivo NDJSON.
        board: Tabuleiro (`Board`) correspondente ao puzzle.
    """
    id: str
    board: Board


_DOT = "."
_ALLOWED_DOT_LINE_RE = re.compile(r"^[1-9\.]{81}$")  # NDJSON 9x9 estrito
_WHITESPACE_ONLY_RE = re.compile(r"^\s*$")


def _strip_bom(s: str) -> str:
    """Remove BOM UTF-8 do início da string, se houver.

    Args:
        s: Texto potencialmente com BOM.

    Returns:
        Texto sem BOM no início.
    """
    return s.lstrip("\ufeff")


def _is_perfect_square(x: int) -> bool:
    """Indica se `x` é quadrado perfeito."""
    if x < 0:
        return False
    r = int(x ** 0.5)
    return r * r == x


def _infer_n_from_len(total_cells: int) -> Size:
    """Infere N a partir do número total de células (size^2 = (N^2)^2).

    Para Sudoku clássico 9x9, total_cells = 81 → size = 9 → N = 3.

    Args:
        total_cells: Número total de caracteres/células.

    Returns:
        Valor de N (ex.: 3 para 9x9).

    Raises:
        ValueError: Se o total não mapear para um tabuleiro N^2 x N^2.
    """
    # total_cells = size^2, e size = N^2
    # => total_cells deve ser quadrado perfeito, e sqrt(total_cells) também.
    if not _is_perfect_square(total_cells):
        raise ValueError(
            f"Total de células ({total_cells}) não é um quadrado perfeito."
        )
    size = int(total_cells ** 0.5)
    if not _is_perfect_square(size):
        raise ValueError(
            f"Dimensão ({size}) não é quadrado perfeito (derivado de {total_cells})."
        )
    n = int(size ** 0.5)
    if n < 1:
        raise ValueError("Valor de N inferido inválido.")
    return n


def _grid_from_linear(
    s: str,
    *,
    empty_char: str = "0",
    allow_dot_as_empty: bool = True,
    strict_internal_spaces: bool = True,
) -> Tuple[Grid, Size]:
    """Converte uma string linear em grid NxN e retorna também N.

    Args:
        s: String linear representando a grade (p. ex. 81 chars).
        empty_char: Caractere que será interpretado como vazio (ex.: "0").
        allow_dot_as_empty: Se True, trata '.' como vazio também.
        strict_internal_spaces: Se True, não são permitidos espaços internos.

    Returns:
        (grid, n): A grade 2D e o valor de N (ex.: 3 para 9x9).

    Raises:
        ValueError: Se houver tamanho inválido, caracteres inválidos
            ou espaços internos quando `strict_internal_spaces` for True.
    """
    s = _strip_bom(s)
    s_stripped = s.strip()

    if strict_internal_spaces:
        # Não permitir espaços internos: se houver diferença após remover
        # espaços em branco no meio, rejeitar.
        if re.search(r"\s", s_stripped):
            # Qualquer whitespace no meio (espaço, \n etc.) invalida.
            raise ValueError("A string linear não pode conter espaços/brancos.")
        linear = s_stripped
    else:
        # Remove todos os brancos para tolerar quebras de linha ocasionais.
        linear = re.sub(r"\s+", "", s_stripped)

    total = len(linear)
    n = _infer_n_from_len(total)
    size = n * n

    allowed = set("123456789")
    # Permitir vazio conforme parâmetros:
    empties = {empty_char}
    if allow_dot_as_empty:
        empties.add(".")

    grid: Grid = []
    idx = 0
    for r in range(size):
        row: List[int] = []
        for c in range(size):
            ch = linear[idx]
            idx += 1
            if ch in empties:
                row.append(EMPTY)
            elif ch in allowed and int(ch) <= size:
                row.append(int(ch))
            else:
                raise ValueError(
                    f"Caractere inválido '{ch}' em (r={r}, c={c}); "
                    f"permitidos: dígitos 1..{size} e {sorted(empties)}."
                )
        grid.append(row)

    return grid, n


# ============================================================================
# Parsing/serialização UNITÁRIOS (um tabuleiro)
# ============================================================================

def parse_txt_compact(puzzle_str: str, *, n: Optional[Size] = None) -> Board:
    """Cria um `Board` a partir de uma string compacta (linear).

    Aceita `0` e '.' como vazios. Por padrão, **não** permite espaços internos.

    Args:
        puzzle_str: String linear (ex.: 81 chars para 9x9).
        n: N explicitamente informado (opcional). Se omitido, será inferido
            a partir do comprimento da string.

    Returns:
        Board: Tabuleiro correspondente.

    Raises:
        ValueError: Se a string contiver caracteres inválidos, tamanho incorreto
            ou espaços internos.
    """
    grid, inferred_n = _grid_from_linear(puzzle_str, empty_char="0", allow_dot_as_empty=True, strict_internal_spaces=True)
    return Board(grid, n=(n or inferred_n))


def to_txt_compact(board: Board, *, empty_char: str = "0") -> str:
    """Serializa um `Board` em string compacta (linear).

    Args:
        board: Tabuleiro de entrada.
        empty_char: Caractere para células vazias (padrão '0').

    Returns:
        String linear no comprimento size^2 (ex.: 81).
    """
    g = board.to_grid()
    chars: List[str] = []
    for row in g:
        for v in row:
            chars.append(str(v) if v != EMPTY else empty_char)
    return "".join(chars)


def parse_txt_grid(puzzle_str: str, *, n: Optional[Size] = None, flex: bool = True) -> Board:
    """Cria um `Board` a partir de uma grade textual (linhas).

    Se `flex=True`, ignora separadores comuns ('|', '-', '+') e espaços,
    aceitando '.' como vazio. Ideal para colar de sites.

    Args:
        puzzle_str: Texto com várias linhas (ex.: 9 linhas de 9).
        n: N explicitamente informado (opcional). Se omitido, será inferido
            a partir do total de células lidas.
        flex: Se True, remove caracteres separadores e espaços.

    Returns:
        Board: Tabuleiro correspondente.

    Raises:
        ValueError: Se dimensões/valores forem inválidos.
    """
    s = _strip_bom(puzzle_str)
    lines = [ln.strip() for ln in s.splitlines() if not _WHITESPACE_ONLY_RE.match(ln)]

    tokens: List[str] = []
    if flex:
        # Remove separadores comuns e espaços.
        sep_re = re.compile(r"[ \t\|\+\-]")
        for ln in lines:
            clean = sep_re.sub("", ln)
            tokens.extend(list(clean))
    else:
        for ln in lines:
            tokens.extend(list(ln))

    linear = "".join(tokens)
    # Para grade, vamos permitir '.' como vazio. Também aceitamos '0'.
    grid, inferred_n = _grid_from_linear(linear, empty_char="0", allow_dot_as_empty=True, strict_internal_spaces=True)
    return Board(grid, n=(n or inferred_n))


def parse_json(puzzle_json: str) -> Board:
    """Cria um `Board` a partir de JSON com `grid` e opcionalmente `n`.

    Estrutura esperada:
        {"grid": [[...],[...],...], "n": 3?}

    Args:
        puzzle_json: String JSON.

    Returns:
        Board: Tabuleiro correspondente.

    Raises:
        ValueError: Se o JSON não contiver `grid` válido ou se `n` for inválido.
    """
    try:
        obj = json.loads(_strip_bom(puzzle_json))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {e}") from e

    if not isinstance(obj, dict) or "grid" not in obj:
        raise ValueError("JSON deve conter objeto com chave 'grid'.")

    grid = obj["grid"]
    if not isinstance(grid, list) or not all(isinstance(r, list) for r in grid):
        raise ValueError("'grid' deve ser lista de listas de inteiros.")

    # Cópia defensiva + coerção de valores
    g2: Grid = []
    for i, row in enumerate(grid):
        row2: List[int] = []
        for j, v in enumerate(row):
            if not isinstance(v, int):
                raise ValueError(f"Valor não-inteiro em grid[{i}][{j}]: {v}")
            row2.append(v)
        g2.append(row2)

    n = obj.get("n", None)
    if n is not None and (not isinstance(n, int) or n < 1):
        raise ValueError(f"Valor inválido para 'n': {n}")

    return Board(g2, n=(n or DEFAULT_N))


def to_json(board: Board, *, include_n: bool = True, pretty: bool = True) -> str:
    """Serializa um `Board` em JSON.

    Args:
        board: Tabuleiro.
        include_n: Se True, inclui chave 'n'.
        pretty: Se True, usa indentação para leitura humana.

    Returns:
        String JSON contendo 'grid' e (opcionalmente) 'n'.
    """
    payload = {"grid": board.to_grid()}
    if include_n:
        payload["n"] = board._n  # acesso intencional ao atributo (metadado do Board)
    return json.dumps(payload, ensure_ascii=False, indent=2 if pretty else None)


# ============================================================================
# NDJSON (lotes por dificuldade, 9x9 estrito com '.' como vazio)
# ============================================================================

def parse_ndjson(ndjson_text: str) -> List[PuzzleEntry]:
    """Converte conteúdo NDJSON (múltiplas linhas) em `PuzzleEntry`s (9x9).

    Especificação adotada (lote, 9x9):
        - Um JSON por linha: {"id": "<string>", "puzzle": "<81 chars 1-9|.>"}
        - `id` obrigatório, **único** dentro do arquivo NDJSON
        - `puzzle` com **81** caracteres, apenas '1'..'9' e '.'
        - '.' representa vazio; **apenas 9x9**
        - Linhas vazias são ignoradas; comentários não são permitidos
        - Codificação UTF-8, sem BOM

    Args:
        ndjson_text: Texto NDJSON.

    Returns:
        Lista de `PuzzleEntry` com `Board`s correspondentes.

    Raises:
        ValueError: Se alguma linha violar o esquema ou houver `id` duplicado.
    """
    entries: List[PuzzleEntry] = []
    seen_ids: set[str] = set()

    for lineno, raw in enumerate(_strip_bom(ndjson_text).splitlines(), start=1):
        line = raw.strip()
        if not line:
            # Linha vazia: ignorar
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"NDJSON inválido na linha {lineno}: {e}") from e

        if not isinstance(obj, dict):
            raise ValueError(f"Linha {lineno}: objeto JSON esperado.")

        if "id" not in obj or "puzzle" not in obj:
            raise ValueError(f"Linha {lineno}: campos obrigatórios 'id' e 'puzzle' ausentes.")

        pid = obj["id"]
        puzzle = obj["puzzle"]

        if not isinstance(pid, str) or not pid:
            raise ValueError(f"Linha {lineno}: 'id' deve ser string não-vazia.")
        if pid in seen_ids:
            raise ValueError(f"Linha {lineno}: 'id' duplicado no arquivo: {pid}")
        seen_ids.add(pid)

        if not isinstance(puzzle, str):
            raise ValueError(f"Linha {lineno}: 'puzzle' deve ser string.")
        if not _ALLOWED_DOT_LINE_RE.match(puzzle):
            raise ValueError(
                f"Linha {lineno}: 'puzzle' deve ter 81 caracteres com apenas '1'..'9' e '.'."
            )

        # Converter '.' → 0 e montar Board 9x9 (N=3).
        grid, n = _grid_from_linear(
            puzzle,
            empty_char="0",
            allow_dot_as_empty=True,
            strict_internal_spaces=True,
        )
        # Em NDJSON, especificação é 9x9; garantir N=3:
        if n != 3:
            raise ValueError(
                f"Linha {lineno}: NDJSON é restrito a 9x9 (N=3). Encontrado N={n}."
            )

        board = Board(grid, n=3)
        entries.append(PuzzleEntry(id=pid, board=board))

    return entries


def load_ndjson(path: str | Path) -> List[PuzzleEntry]:
    """Carrega um arquivo NDJSON (UTF-8) e retorna `PuzzleEntry`s (9x9).

    Args:
        path: Caminho do arquivo NDJSON.

    Returns:
        Lista de puzzles com metadados (id + board).

    Raises:
        ValueError: Em caso de violação do esquema/duplicidade de id.
        FileNotFoundError: Se o arquivo não existir.
    """
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return parse_ndjson(text)


def save_ndjson(path: str | Path, entries: Sequence[PuzzleEntry]) -> None:
    """Salva uma lista de `PuzzleEntry` em NDJSON (UTF-8, sem BOM).

    Cada linha conterá:
        {"id":"<id>","puzzle":"<81 chars 1-9|.>"}

    Regras:
        - `id` deve ser único na sequência fornecida (checado aqui)
        - `puzzle` será gerado a partir do `Board` usando '.' como vazio
          e deve resultar em 81 caracteres (9x9).

    Args:
        path: Caminho do arquivo de saída.
        entries: Sequência de puzzles.

    Raises:
        ValueError: Se houver `id` duplicado ou tabuleiro não-9x9.
    """
    seen: set[str] = set()
    lines: List[str] = []
    for e in entries:
        if e.id in seen:
            raise ValueError(f"id duplicado na sequência: {e.id}")
        seen.add(e.id)
        # Garantir 9x9 (N=3)
        size = e.board.size()
        if size != 9:
            raise ValueError(f"Apenas 9x9 é suportado para NDJSON (encontrado {size}x{size}).")
        puzzle = to_txt_compact(e.board, empty_char=_DOT)
        if len(puzzle) != 81 or not _ALLOWED_DOT_LINE_RE.match(puzzle):
            raise ValueError(f"Tabuleiro inválido ao serializar NDJSON para id={e.id}.")
        obj = {"id": e.id, "puzzle": puzzle}
        lines.append(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))

    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ============================================================================
# Carregadores/gravadores de ARQUIVOS unitários (conveniência)
# ============================================================================

def load_txt(path: str | Path, *, compact: bool | None = None) -> Board:
    """Carrega um puzzle TXT e cria um `Board`.

    Modos:
        - `compact=True`: interpreta como string linear (ex.: 81 chars).
        - `compact=False`: interpreta como grade (linhas).
        - `compact=None` (padrão): tenta detectar automaticamente
          (primeiro tenta "compacto"; se falhar, tenta "grid").

    Args:
        path: Caminho do arquivo TXT.
        compact: Modo de parsing.

    Returns:
        Board: Tabuleiro correspondente.

    Raises:
        ValueError: Se o conteúdo não casar com os formatos esperados.
        FileNotFoundError: Se o arquivo não existir.
    """
    text = Path(path).read_text(encoding="utf-8")
    err_compact: Optional[Exception] = None
    err_grid: Optional[Exception] = None

    if compact is True:
        return parse_txt_compact(text)

    if compact is False:
        return parse_txt_grid(text, flex=True)

    # Auto: tenta compacto, depois grid.
    try:
        return parse_txt_compact(text)
    except Exception as e:
        err_compact = e
    try:
        return parse_txt_grid(text, flex=True)
    except Exception as e:
        err_grid = e

    raise ValueError(
        f"Falha ao interpretar TXT.\n"
        f"- Erro (compacto): {err_compact}\n"
        f"- Erro (grid): {err_grid}"
    )


def save_txt_compact(board: Board, path: str | Path, *, empty_char: str = "0") -> None:
    """Grava um `Board` em TXT no formato compacto (linear)."""
    text = to_txt_compact(board, empty_char=empty_char)
    Path(path).write_text(text + "\n", encoding="utf-8")


def save_txt_grid(board: Board, path: str | Path, *, empty_char: str = ".") -> None:
    """Grava um `Board` em TXT no formato grid (linhas)."""
    Path(path).write_text(to_txt_grid(board, empty_char=empty_char) + "\n", encoding="utf-8")


def load_json(path: str | Path) -> Board:
    """Carrega um puzzle a partir de um arquivo JSON (objeto)."""
    text = Path(path).read_text(encoding="utf-8")
    return parse_json(text)


def save_json(board: Board, path: str | Path, *, include_n: bool = True, pretty: bool = True) -> None:
    """Grava um `Board` em JSON (objeto)."""
    Path(path).write_text(to_json(board, include_n=include_n, pretty=pretty) + "\n", encoding="utf-8")


# ============================================================================
# Serialização em grade (visual)
# ============================================================================

def to_txt_grid(board: Board, *, empty_char: str = ".") -> str:
    """Serializa um `Board` em formato de grade (linhas).

    Usa `empty_char` para células vazias (padrão '.').

    Args:
        board: Tabuleiro de entrada.
        empty_char: Caractere para vazio (padrão '.').

    Returns:
        Texto com `size` linhas, cada uma com `size` células separadas por espaço.
    """
    size = board.size()
    g = board.to_grid()

    def fmt_row(row: Sequence[int]) -> str:
        return " ".join(str(v) if v != EMPTY else empty_char for v in row)

    return "\n".join(fmt_row(row) for row in g)


"""Representação de tabuleiro (Board) para Sudoku.

O `Board` é a *fonte de verdade* do estado do jogo: armazena a grade N²×N²,
expondo operações seguras de leitura e escrita, além de utilitários de cópia
e serialização. Ele **não** valida regras do Sudoku (linhas/colunas/caixas):
isso é responsabilidade de componentes de validação/solução (ex.: `SudokuRules`
e os solvers). Essa separação respeita SOLID (SRP) e facilita testes e evolução.

Decisões de design principais:
- **Separação de responsabilidades:** `Board` apenas gerencia estado.
- **Segurança:** impede alterações nas *pistas iniciais* (“givens”).
- **API estável:** leitura (`get`), escrita (`set`/`with_value`), cópias (`clone`),
  e serialização (`to_grid`), mais utilitários como `is_full`/`is_given`.
- **Generalidade:** parametrizado por `n` (ex.: `n=3` → 9×9; `n=4` → 16×16).
"""

from __future__ import annotations

from typing import Sequence

from .types import Grid, Digit, Size, DEFAULT_N, EMPTY


class Board:
    """Contêiner de estado de um tabuleiro de Sudoku.

    Um `Board` guarda a grade e conhece:
    - o tamanho lógico `size = n * n` (ex.: 9 quando `n=3`);
    - quais células são *pistas iniciais* (não podem ser alteradas).

    **Importante:** este componente **não** verifica se uma jogada mantém
    o tabuleiro válido segundo as regras do Sudoku. A validação pertence
    a outro módulo (ex.: `SudokuRules`). Aqui garantimos apenas:
    - integridade estrutural (índices e faixa de dígitos),
    - imutabilidade de *givens*.

    Attributes:
        _grid (list[list[int]]): Grade 2D interna do tabuleiro.
        _n (int): Parâmetro N (3 para 9x9, 4 para 16x16, etc.).
        _size (int): Dimensão total da grade (N*N).
        _given (list[list[bool]]): Máscara booleana das pistas iniciais.
    """

    # --------------------------------------------------------------------- #
    # Construção e informações básicas
    # --------------------------------------------------------------------- #

    def __init__(self, grid: Grid, n: Size = DEFAULT_N) -> None:
        """Inicializa o tabuleiro com uma grade e parâmetro N.

        Cria cópias internas para evitar aliasing de listas externas e
        marca como *pistas iniciais* todas as células não vazias do grid
        fornecido. Células marcadas como *given* não podem ser alteradas.

        **Não** executa verificação de regras do Sudoku (duplicidades etc.).

        Args:
            grid: Grade inicial; use `0` (constante `EMPTY`) para células vazias.
            n: Parâmetro N; `n=3` => 9×9.

        Raises:
            ValueError: Se `n < 1`, se a grade não for N²×N²,
                ou se houver dígitos fora da faixa [0, N²].
        """
        if n < 1:
            raise ValueError("Parameter `n` must be >= 1.")

        self._n: int = int(n)
        self._size: int = self._n * self._n

        # Cópia defensiva do grid recebido (linhas novas).
        self._grid: list[list[int]] = [list(row) for row in grid]

        # Valida dimensão e faixa de dígitos (integridade estrutural).
        self._validate_shape(self._grid)
        self._validate_values(self._grid)

        # Máscara de pistas iniciais (células != EMPTY).
        self._given: list[list[bool]] = [
            [cell != EMPTY for cell in row] for row in self._grid
        ]

    # --------------------------------------------------------------------- #
    # Leitura, escrita e utilitários
    # --------------------------------------------------------------------- #

    def size(self) -> int:
        """Retorna a dimensão da grade (N*N).

        Returns:
            int: Dimensão da grade (ex.: 9 para `n=3`).
        """
        return self._size

    def get(self, r: int, c: int) -> Digit:
        """Obtém o valor na célula (r, c).

        Não executa verificação de regras do Sudoku; apenas leitura segura.

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).

        Returns:
            Dígito na célula; `0` (EMPTY) indica vazio.

        Raises:
            IndexError: Se (r, c) estiver fora dos limites.
        """
        self._check_bounds(r, c)
        return self._grid[r][c]

    def set(self, r: int, c: int, v: Digit) -> None:
        """Define o valor da célula (r, c) *mutando* este `Board`.

        **Não** valida regras de Sudoku; garante apenas:
        - índices válidos,
        - dígito na faixa [0, size],
        - célula não marcada como *given* (pista inicial).

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).
            v: Dígito desejado (0 para limpar).

        Raises:
            IndexError: Se (r, c) estiver fora dos limites.
            ValueError: Se `v` estiver fora da faixa [0, size].
            PermissionError: Se a célula for uma pista inicial (*given*).
        """
        self._check_bounds(r, c)
        self._check_digit(v)
        if self._given[r][c]:
            raise PermissionError(
                f"Cannot modify a given cell at (r={r}, c={c})."
            )
        self._grid[r][c] = v

    def with_value(self, r: int, c: int, v: Digit) -> "Board":
        """Retorna um **novo** `Board` com (r, c) = v (sem alterar o atual).

        Útil em cenários funcionais (ex.: busca e simulação de jogadas),
        evitando efeitos colaterais. Aplica as mesmas garantias de `set`.

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).
            v: Dígito desejado (0 para limpar).

        Returns:
            Board: Nova instância com a célula alterada.

        Raises:
            IndexError: Se (r, c) estiver fora dos limites.
            ValueError: Se `v` estiver fora da faixa [0, size].
            PermissionError: Se a célula for uma pista inicial (*given*).
        """
        self._check_bounds(r, c)
        self._check_digit(v)
        if self._given[r][c]:
            raise PermissionError(
                f"Cannot modify a given cell at (r={r}, c={c})."
            )
        new_grid = self.to_grid()
        new_grid[r][c] = v
        # As pistas iniciais são derivadas do grid inicial: continuam as mesmas.
        # Como o construtor marca givens a partir do grid recebido,
        # ao criar um novo Board com o grid alterado, mantemos a regra
        # de que apenas as células originalmente vazias são editáveis.
        return Board(new_grid, n=self._n)

    def is_full(self) -> bool:
        """Indica se todas as células estão preenchidas (≠ EMPTY).

        **Observação:** não implica tabuleiro resolvido; apenas ausência de vazios.

        Returns:
            True se não houver `EMPTY` na grade; False caso contrário.
        """
        for row in self._grid:
            for v in row:
                if v == EMPTY:
                    return False
        return True

    def is_given(self, r: int, c: int) -> bool:
        """Informa se a célula (r, c) é uma pista inicial (*given*).

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).

        Returns:
            True se a célula foi definida no grid inicial; False caso contrário.

        Raises:
            IndexError: Se (r, c) estiver fora dos limites.
        """
        self._check_bounds(r, c)
        return self._given[r][c]

    def to_grid(self) -> Grid:
        """Retorna uma cópia profunda da grade interna.

        Útil para serialização, IO e integração com UI sem expor estado interno.

        Returns:
            Grid: Nova lista de listas com os mesmos valores.
        """
        return [row.copy() for row in self._grid]

    def clone(self) -> "Board":
        """Cria uma cópia independente deste `Board`.

        A cópia preserva `n`, a grade e as pistas iniciais (por construção).

        Returns:
            Board: Nova instância independente.
        """
        return Board(self.to_grid(), n=self._n)

    # --------------------------------------------------------------------- #
    # Representações (depuração)
    # --------------------------------------------------------------------- #

    def __repr__(self) -> str:
        """Representação detalhada para depuração.

        Returns:
            str: String com `n`, `size` e uma prévia da grade.
        """
        preview_rows = 3 if self._size >= 3 else self._size
        preview = "; ".join(
            " ".join(str(v) for v in self._grid[r][: min(self._size, 6)])
            for r in range(preview_rows)
        )
        return f"Board(n={self._n}, size={self._size}, preview=[{preview}])"

    def __str__(self) -> str:
        """Representação amigável em múltiplas linhas.

        Substitui zeros por pontos para facilitar visualização.

        Returns:
            str: Grade formatada linha a linha.
        """
        def fmt_row(row: list[int]) -> str:
            return " ".join(str(v) if v != EMPTY else "." for v in row)

        return "\n".join(fmt_row(row) for row in self._grid)

    # --------------------------------------------------------------------- #
    # Validações e checagens internas
    # --------------------------------------------------------------------- #

    def _validate_shape(self, grid: Grid) -> None:
        """Valida se `grid` possui dimensão N²×N².

        Args:
            grid: Grade a ser verificada.

        Raises:
            ValueError: Se a quantidade de linhas/colunas não for N².
        """
        if len(grid) != self._size:
            raise ValueError(
                f"Grid must have {self._size} rows (got {len(grid)})."
            )
        for i, row in enumerate(grid):
            if len(row) != self._size:
                raise ValueError(
                    f"Row {i} must have {self._size} columns (got {len(row)})."
                )

    def _validate_values(self, grid: Grid) -> None:
        """Valida se todos os dígitos estão na faixa [0, N²].

        **Não** verifica regras de Sudoku, apenas integridade de faixa.

        Args:
            grid: Grade a ser verificada.

        Raises:
            ValueError: Se algum dígito estiver fora da faixa permitida.
        """
        min_v, max_v = 0, self._size
        for r, row in enumerate(grid):
            for c, v in enumerate(row):
                if not (min_v <= v <= max_v):
                    raise ValueError(
                        f"Digit out of range at (r={r}, c={c}): {v} "
                        f"(allowed {min_v}..{max_v})."
                    )

    def _check_bounds(self, r: int, c: int) -> None:
        """Garante que (r, c) estão dentro dos limites do tabuleiro.

        Args:
            r: Índice da linha (0-index).
            c: Índice da coluna (0-index).

        Raises:
            IndexError: Se (r, c) estiver fora dos limites.
        """
        if not (0 <= r < self._size) or not (0 <= c < self._size):
            raise IndexError(
                f"Cell index out of bounds: (r={r}, c={c}) for size {self._size}."
            )

    def _check_digit(self, v: Digit) -> None:
        """Garante que o dígito está na faixa [0, N²].

        Args:
            v: Dígito a ser verificado.

        Raises:
            ValueError: Se `v` estiver fora da faixa.
        """
        if not (0 <= v <= self._size):
            raise ValueError(
                f"Digit out of range: {v} (allowed 0..{self._size})."
            )


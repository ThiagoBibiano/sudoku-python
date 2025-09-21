"""Registro simples de solvers.

Responsabilidades:
- Registrar e recuperar implementações de Solver por nome.
- Facilitar seleção via UI (Streamlit) sem acoplamento.

Nesta etapa, apenas assinaturas.
"""

from __future__ import annotations
from typing import Dict, Type
from .base import Solver


def register(name: str, solver_cls: Type[Solver]) -> None:
    """Registra uma classe de solver por nome.

    Args:
        name: Nome curto do solver (ex.: "backtracking").
        solver_cls: Classe concreta que implementa Solver.
    """
    raise NotImplementedError


def get(name: str) -> Type[Solver]:
    """Obtém a classe de solver registrada pelo nome.

    Args:
        name: Nome curto do solver.

    Returns:
        Classe de solver correspondente.

    Raises:
        KeyError: Se o nome não estiver registrado.
    """
    raise NotImplementedError


def all_registered() -> Dict[str, Type[Solver]]:
    """Retorna o mapeamento completo de solvers registrados.

    Returns:
        Dicionário {nome: classe}.
    """
    raise NotImplementedError


"""Registro simples de solvers.

Responsabilidades:
- Registrar e recuperar implementações de Solver por nome.
- Facilitar seleção via UI (Streamlit) sem acoplamento.

Nesta etapa, apenas assinaturas.
"""

from __future__ import annotations
from typing import Dict, Type

from .base import Solver

_REGISTRY: Dict[str, Type[Solver]] = {}


def register(name: str, solver_cls: Type[Solver]) -> None:
    """Registra uma classe de solver por nome.

    Args:
        name: Nome curto do solver (ex.: "backtracking").
        solver_cls: Classe concreta que implementa Solver.
    """
    if not issubclass(solver_cls, Solver):
        raise TypeError("solver_cls must be a subclass of Solver.")
    if name in _REGISTRY:
        raise ValueError(f"Solver '{name}' is already registered.")
    _REGISTRY[name] = solver_cls


def get(name: str) -> Type[Solver]:
    """Obtém a classe de solver registrada pelo nome.

    Args:
        name: Nome curto do solver.

    Returns:
        Classe de solver correspondente.

    Raises:
        KeyError: Se o nome não estiver registrado.
    """
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        raise KeyError(f"Solver '{name}' is not registered.") from exc


def all_registered() -> Dict[str, Type[Solver]]:
    """Retorna o mapeamento completo de solvers registrados.

    Returns:
        Dicionário {nome: classe}.
    """
    return dict(_REGISTRY)

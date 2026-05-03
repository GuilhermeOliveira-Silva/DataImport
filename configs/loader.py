"""
configs/loader.py
Carrega configurações dinâmicas para importação.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace


def carregar_config(nome: str):
    """
    Carrega o módulo de configuração em configs.<nome>.

    Atributos obrigatórios: COLUNAS_BANCO, MAPA_COLUNAS, COLUNAS_OBRIGATORIAS
    Atributos opcionais:
        NORMALIZADORES   — dict col → função ou nome de função
        POS_PROCESSADOR  — função(df) → df, aplicada após NORMALIZADORES
    """
    try:
        modulo = importlib.import_module(f"configs.{nome}")
    except ModuleNotFoundError as exc:
        raise ValueError(f"Configuração '{nome}' não encontrada em configs/") from exc

    obrigatorios = ["COLUNAS_BANCO", "MAPA_COLUNAS", "COLUNAS_OBRIGATORIAS"]
    faltando = [attr for attr in obrigatorios if not hasattr(modulo, attr)]
    if faltando:
        raise ValueError(
            f"Configuração '{nome}' incompleta. Faltando: {faltando}"
        )

    return SimpleNamespace(
        COLUNAS_BANCO=modulo.COLUNAS_BANCO,
        MAPA_COLUNAS=modulo.MAPA_COLUNAS,
        COLUNAS_OBRIGATORIAS=modulo.COLUNAS_OBRIGATORIAS,
        NORMALIZADORES=getattr(modulo, "NORMALIZADORES", None),
        POS_PROCESSADOR=getattr(modulo, "POS_PROCESSADOR", None),
    )
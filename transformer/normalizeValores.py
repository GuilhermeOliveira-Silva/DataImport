"""
transformer/normalizer.py
Responsabilidade: Limpeza e normalização automática dos dados vindos da Parte 1.
Não lança exceções — apenas corrige o que for possível corrigir.
"""

import re
import pandas as pd


# =============================================================================
# NORMALIZAÇÃO INDIVIDUAL POR TIPO
# =============================================================================

def normalizar_cpf(valor: str) -> str:
    """Remove tudo que não for dígito. '123.456.789-09' → '12345678909'"""
    if pd.isna(valor):
        return valor
    return re.sub(r"\D", "", str(valor))


def normalizar_telefone(valor: str) -> str:
    """Remove tudo que não for dígito. '(11) 9 8765-4321' → '11987654321'"""
    if pd.isna(valor):
        return valor
    return re.sub(r"\D", "", str(valor))


def normalizar_data(valor: str) -> str:
    """
    Tenta converter datas variadas para YYYY-MM-DD.
    Aceita formatos comuns: DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD, etc.
    Retorna o valor original se não conseguir converter.
    """
    if pd.isna(valor) or str(valor).strip() == "":
        return valor
    try:
        return pd.to_datetime(str(valor), dayfirst=True, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return valor  # mantém original — a validação vai capturar se necessário


def normalizar_sexo(valor: str) -> str:
    """
    Masculino / MASCULINO / masculino / M → 'M'
    Feminino  / FEMININO  / feminino  / F → 'F'
    Qualquer outro valor → mantém original (validação posterior decide)
    """
    if pd.isna(valor):
        return valor
    mapa = {
        "m": "M", "masculino": "M",
        "f": "F", "feminino": "F",
    }
    return mapa.get(str(valor).strip().lower(), str(valor).strip())


def normalizar_string(valor: str) -> str:
    """Remove espaços no início e fim."""
    if pd.isna(valor):
        return valor
    return str(valor).strip()


# =============================================================================
# NORMALIZAÇÃO DO DATAFRAME COMPLETO
# =============================================================================

def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe o DataFrame da Parte 1 e aplica todas as normalizações.
    Opera sobre uma cópia — não modifica o DataFrame original.

    Returns:
        pd.DataFrame com dados normalizados.
    """
    df = df.copy()

    # Strings: todas as colunas de texto recebem strip()
    colunas_string = df.select_dtypes(include="object").columns
    for col in colunas_string:
        df[col] = df[col].apply(normalizar_string)

    # Campos específicos
    if "CPF" in df.columns:
        df["CPF"] = df["CPF"].apply(normalizar_cpf)

    for col_tel in ["NRO_CELULAR", "NRO_FONE1", "NRO_FONE2"]:
        if col_tel in df.columns:
            df[col_tel] = df[col_tel].apply(normalizar_telefone)

    if "DT_NASCIMENTO" in df.columns:
        df["DT_NASCIMENTO"] = df["DT_NASCIMENTO"].apply(normalizar_data)

    if "SEXO" in df.columns:
        df["SEXO"] = df["SEXO"].apply(normalizar_sexo)

    return df
"""
configs/agendamentos.py
Configurações e normalizações para importação de AGENDAMENTOS.
"""

from datetime import datetime, timedelta

# =============================================================================
# SCHEMA
# =============================================================================

COLUNAS_BANCO = [
    "DATA",
    "FROMTIME",
    "TOTIME",
    "TEMPO",
    "PACIENTE",
    "OBSERVACAO",
    "ID_STATUS",
    "ID_ESPECIALIDADE",
    "ID_PROFISSIONAL",
    "DATA_CRIACAO",
]

COLUNAS_OBRIGATORIAS = ["ID_STATUS"]

MAPA_COLUNAS = {
    "data": "DATA",
    "data_agendamento": "DATA",

    "fromtime": "FROMTIME",
    "hora_inicio": "FROMTIME",
    "inicio": "FROMTIME",

    "totime": "TOTIME",
    "hora_fim": "TOTIME",
    "fim": "TOTIME",

    "tempo": "TEMPO",
    "duracao": "TEMPO",

    "paciente": "PACIENTE",
    "nome": "PACIENTE",

    "observacao": "OBSERVACAO",
    "obs": "OBSERVACAO",

    "id_status": "ID_STATUS",
    "status": "ID_STATUS",

    "especialidade": "ID_ESPECIALIDADE",
    "id_especialidade": "ID_ESPECIALIDADE",

    "profissional": "ID_PROFISSIONAL",
    "id_profissional": "ID_PROFISSIONAL",

    "data_criacao": "DATA_CRIACAO",
}


# =============================================================================
# NORMALIZADORES SIMPLES
# =============================================================================

def normalizar_status(valor) -> str:
    """Vazio → '1' (ativo por padrão)."""
    if valor is None:
        return "1"
    return str(valor)


def normalizar_paciente(valor) -> str | None:
    """Strip e vazio → None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto if texto else None


def normalizar_especialidade(valor) -> str | None:
    """Mapeia textos conhecidos; vazio → None."""
    if valor is None:
        return None
    texto = str(valor).strip().lower()
    if not texto:
        return None
    if "clinico" in texto:
        return "1"
    if "orto" in texto:
        return "10"
    return None


# =============================================================================
# NORMALIZADOR DE HORÁRIOS E TEMPO (row-level)
# Regras:
#   CASO 1 — FROMTIME presente, TOTIME ausente → TOTIME = None, TEMPO calculado se possível
#   CASO 2 — só TEMPO presente                 → FROMTIME e TOTIME ficam None
#   CASO 3 — FROMTIME e TOTIME presentes       → calcula TEMPO pela diferença
#   CASO 4 — nenhum presente                   → tudo None
#
# TOTIME NUNCA é preenchido automaticamente — se vier vazio, fica None.
# =============================================================================

def _parse_hora(h) -> datetime | None:
    """Tenta parsear HH:MM ou HH:MM:SS. Retorna None se inválido."""
    if not h or str(h).strip() in ("", "None", "nan"):
        return None
    texto = str(h).strip()[:5]  # pega só HH:MM
    try:
        return datetime.strptime(texto, "%H:%M")
    except ValueError:
        return None


def normalizar_horarios_e_tempo(row) -> tuple[str | None, str | None, str | None]:
    """
    Recebe uma linha do DataFrame e retorna (FROMTIME, TOTIME, TEMPO).

    TOTIME nunca é calculado automaticamente — se vier vazio, permanece None.
    """
    ft = _parse_hora(row.get("FROMTIME"))
    tt = _parse_hora(row.get("TOTIME"))
    tempo_raw = row.get("TEMPO")
    tempo = str(tempo_raw).strip() if tempo_raw and str(tempo_raw).strip() not in ("", "None", "nan") else None

    fromtime_str = ft.strftime("%H:%M") if ft else None
    totime_str   = tt.strftime("%H:%M") if tt else None  # None se vier vazio

    # CASO 3 — ambos presentes → calcula TEMPO pela diferença
    if ft and tt:
        diff = int((tt - ft).total_seconds() / 60)
        return fromtime_str, totime_str, str(diff)

    # CASO 2 — só TEMPO presente
    if tempo and not ft and not tt:
        return None, None, tempo

    # CASO 1 — só FROMTIME presente (TOTIME fica None)
    if ft and not tt:
        return fromtime_str, None, tempo or "30"

    # CASO 4 — nenhum presente
    return None, None, tempo or "30"


# =============================================================================
# NORMALIZADORES POR COLUNA
# =============================================================================

NORMALIZADORES = {
    "PACIENTE":        normalizar_paciente,
    "ID_STATUS":       normalizar_status,
    "ID_ESPECIALIDADE": normalizar_especialidade,
}

# =============================================================================
# PÓS-PROCESSAMENTO (aplicado pelo motor após NORMALIZADORES)
# Responsável pela lógica row-level de FROMTIME / TOTIME / TEMPO.
# =============================================================================

def pos_processar(df):
    """
    Aplica normalizar_horarios_e_tempo linha a linha.
    Chamado pelo motor após aplicar NORMALIZADORES.
    """
    import pandas as pd
    resultado = df.apply(
        lambda row: normalizar_horarios_e_tempo(row.to_dict()),
        axis=1,
        result_type="expand",
    )
    resultado.columns = ["FROMTIME", "TOTIME", "TEMPO"]
    df[["FROMTIME", "TOTIME", "TEMPO"]] = resultado
    return df


POS_PROCESSADOR = pos_processar
"""
configs/procedimentos.py
Configurações e normalizações para importação de PROCEDIMENTOS.
"""

COLUNAS_BANCO = [
    "ID_TABELA_SERVICO",
    "ID_ESPECIALIDADE",
    "CODIGO_CONVENIO",
    "DESCRICAO",
    "VALOR",
    "VALOR_LABORATORIO",
    "GERA_COMISSAO",
    "GERA_ATENDIMENTO",
]

MAPA_COLUNAS = {
    # DESCRICAO
    "descricao": "DESCRICAO",
    "nome": "DESCRICAO",

    # VALOR
    "valor": "VALOR",
    "preco": "VALOR",

    # CODIGO_CONVENIO
    "codigo": "CODIGO_CONVENIO",
    "codigo_convenio": "CODIGO_CONVENIO",
    "tuss": "CODIGO_CONVENIO",

    # ID_ESPECIALIDADE — nome exato do banco (após lowercase) + sinônimos
    "id_especialidade": "ID_ESPECIALIDADE",
    "especialidade": "ID_ESPECIALIDADE",

    # ID_TABELA_SERVICO — nome exato do banco (após lowercase) + sinônimos
    "id_tabela_servico": "ID_TABELA_SERVICO",
    "tabela": "ID_TABELA_SERVICO",
    "tabela_servico": "ID_TABELA_SERVICO",

    # FLAGS
    "gera_comissao": "GERA_COMISSAO",
    "gera_atendimento": "GERA_ATENDIMENTO",
}

COLUNAS_OBRIGATORIAS = [
    "ID_TABELA_SERVICO",
    "ID_ESPECIALIDADE",
]


# =============================================================================
# NORMALIZADORES
# =============================================================================

def normalizar_valor(valor):
    """Remove R$ e troca vírgula por ponto. Vazio → None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    if texto == "":
        return None
    texto = texto.replace("R$", "").replace(" ", "")
    return texto.replace(",", ".")


def normalizar_id_especialidade(valor):
    """Mapeia textos conhecidos; vazio → None."""
    if valor is None:
        return None
    texto = str(valor).strip().lower()
    if texto == "":
        return None
    if texto == "clinico geral":
        return "1"
    if texto == "orto":
        return "10"
    return valor


def normalizar_id_tabela_servico(valor):
    """Vazio → None."""
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto == "" else valor


def normalizar_valor_laboratorio(_valor):
    """Sempre retorna None."""
    return None


def normalizar_gera_comissao(valor):
    """Vazio → 1."""
    if valor is None:
        return "1"
    texto = str(valor).strip()
    return "1" if texto == "" else valor


def normalizar_gera_atendimento(valor):
    """Vazio → 1."""
    if valor is None:
        return "1"
    texto = str(valor).strip()
    return "1" if texto == "" else valor


NORMALIZADORES = {
    "ID_ESPECIALIDADE":   normalizar_id_especialidade,
    "ID_TABELA_SERVICO":  normalizar_id_tabela_servico,
    "VALOR":              normalizar_valor,
    "VALOR_LABORATORIO":  normalizar_valor_laboratorio,
    "GERA_COMISSAO":      normalizar_gera_comissao,
    "GERA_ATENDIMENTO":   normalizar_gera_atendimento,
}
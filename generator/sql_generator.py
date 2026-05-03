"""
generator/sql_generator.py
Responsabilidade: Gerar comandos SQL INSERT em lote a partir do DataFrame validado.
Otimizado para arquivos grandes (100k+ linhas).
"""

import pandas as pd
from pathlib import Path


# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

TABELA_PADRAO  = "PACIENTES"
NOME_ARQUIVO   = "inserts_pacientes.txt"
TAMANHO_LOTE   = 500

COLUNAS_EXCLUIR   = {"ID"}
COLUNAS_NUMERICAS = {"ID_CLINICA", "STATUS"}

# Strings que representam nulo e devem virar NULL no SQL
_STRINGS_NULAS = {"", "nan", "none", "null", "na", "<na>", "n/a", "nd", "-", "nat"}


# =============================================================================
# FORMATAÇÃO DE VALORES
# =============================================================================

def _formatar_valor(valor, coluna: str) -> str:
    """
    Converte um valor Python para a representação SQL correta.
    """
    # 1. None puro
    if valor is None:
        return "NULL"

    # 2. float NaN
    if isinstance(valor, float) and pd.isna(valor):
        return "NULL"

    # 3. pd.NA, pd.NaT e outros escalares pandas
    try:
        if pd.isna(valor):
            return "NULL"
    except (TypeError, ValueError):
        pass

    # 4 e 5. Strings residuais
    valor_str = str(valor).strip()
    if valor_str.lower() in _STRINGS_NULAS:
        return "NULL"

    # Numérico — sem aspas
    if coluna in COLUNAS_NUMERICAS:
        if valor_str.lstrip("-").replace(".", "", 1).isdigit():
            return valor_str
        # Não é número mesmo sendo coluna numérica → trata como texto
        return "'" + valor_str.replace("'", "''") + "'"

    # Texto — aspas simples escapadas
    return "'" + valor_str.replace("'", "''") + "'"


# =============================================================================
# GERAÇÃO DO SQL
# =============================================================================

def _linha_para_valores(row: pd.Series, colunas: list[str]) -> str:
    """Converte uma linha do DataFrame em '(val1, val2, ...)' para o INSERT."""
    return "(" + ", ".join(_formatar_valor(row[col], col) for col in colunas) + ")"


def gerar_sql(df: pd.DataFrame, tabela: str = TABELA_PADRAO) -> str:
    """
    Gera todos os INSERTs em lote como uma única string SQL.
    Cada lote de TAMANHO_LOTE linhas vira um INSERT INTO ... VALUES (...),(...),...;

    Args:
        df:     DataFrame validado e normalizado.
        tabela: Nome da tabela destino.
    """
    colunas = [c for c in df.columns if c not in COLUNAS_EXCLUIR]
    cabecalho = f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES\n"

    blocos_sql = []
    total_linhas = len(df)

    for inicio in range(0, total_linhas, TAMANHO_LOTE):
        lote = df.iloc[inicio: inicio + TAMANHO_LOTE]
        linhas_valores = lote.apply(
            lambda row: _linha_para_valores(row, colunas), axis=1
        ).tolist()

        blocos_sql.append(cabecalho + ",\n".join(linhas_valores) + ";\n")

        pct = min(inicio + TAMANHO_LOTE, total_linhas)
        print(f"      Gerado: {pct}/{total_linhas} linhas ({100 * pct // total_linhas}%)")

    return "\n".join(blocos_sql)


# =============================================================================
# SALVAMENTO
# =============================================================================

def salvar_sql(sql: str, pasta: str, nome: str = NOME_ARQUIVO) -> str:
    """Salva o SQL na pasta de execução e retorna o caminho completo."""
    caminho = str(Path(pasta) / nome)
    Path(pasta).mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(sql)
    print(f"      💾 SQL salvo em: {caminho}")
    return caminho


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def gerar_e_salvar(df: pd.DataFrame, pasta: str, tabela: str = TABELA_PADRAO) -> str:
    """
    Ponto de entrada da Parte 3.

    Args:
        df:     DataFrame validado (saída da Parte 2).
        pasta:  Pasta de execução (gerada pelo path_manager).
        tabela: Nome da tabela destino (vindo do --tabela do CLI).

    Returns:
        Caminho do arquivo gerado.
    """
    print(f"      Tabela: {tabela} | Linhas: {len(df)} | Lote: {TAMANHO_LOTE}")
    sql = gerar_sql(df, tabela=tabela)
    return salvar_sql(sql, pasta)
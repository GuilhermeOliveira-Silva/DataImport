"""
validator/validator.py
Responsabilidade: Validar regras de negócio após a normalização.
Motor genérico — valida obrigatórias da config + regras específicas por coluna.
"""

import pandas as pd
from dataclasses import dataclass, field


# =============================================================================
# ESTRUTURAS DE RESULTADO
# =============================================================================

@dataclass
class ResultadoValidacao:
    erros:  list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    @property
    def valido(self) -> bool:
        return len(self.erros) == 0

    def resumo(self) -> str:
        linhas = []
        if self.erros:
            linhas.append(f"❌ {len(self.erros)} erro(s) crítico(s):")
            linhas.extend(f"   • {e}" for e in self.erros)
        if self.avisos:
            linhas.append(f"⚠️  {len(self.avisos)} aviso(s):")
            linhas.extend(f"   • {a}" for a in self.avisos)
        if self.valido and not self.avisos:
            linhas.append("✅ Validação passou sem erros ou avisos.")
        return "\n".join(linhas)


# =============================================================================
# VALIDAÇÕES GENÉRICAS (funcionam para qualquer config)
# =============================================================================

def _validar_obrigatorios(
    df: pd.DataFrame,
    resultado: ResultadoValidacao,
    colunas_obrigatorias: list[str],
) -> None:
    """Valida as colunas obrigatórias da config — genérico para qualquer tabela."""
    for col in colunas_obrigatorias:
        if col not in df.columns or df[col].replace("", pd.NA).isna().all():
            resultado.erros.append(
                f"Coluna obrigatória '{col}' está ausente ou completamente vazia."
            )


def _avisar_obrigatorios_parcialmente_vazios(
    df: pd.DataFrame,
    resultado: ResultadoValidacao,
    colunas_obrigatorias: list[str],
) -> None:
    """Avisa se alguma coluna obrigatória tem células vazias (mas não todas)."""
    for col in colunas_obrigatorias:
        if col not in df.columns:
            continue
        vazios = df.index[df[col].replace("", pd.NA).isna()].tolist()
        if vazios:
            linhas = [i + 2 for i in vazios]
            resultado.avisos.append(
                f"'{col}' vazio nas linhas: {linhas}"
            )


# =============================================================================
# VALIDAÇÕES ESPECÍFICAS DE PACIENTES
# =============================================================================

def _validar_nome_paciente(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    if "NOMEPACIENTE" not in df.columns:
        return

    com_numero = df.index[
        df["NOMEPACIENTE"].fillna("").str.contains(r"\d", regex=True)
    ].tolist()
    com_aspas = df.index[
        df["NOMEPACIENTE"].fillna("").str.contains("'", regex=False)
    ].tolist()

    if com_numero:
        resultado.erros.append(
            f"NOMEPACIENTE contém números nas linhas: {[i + 2 for i in com_numero]}"
        )
    if com_aspas:
        resultado.erros.append(
            f"NOMEPACIENTE contém aspas simples (') nas linhas: {[i + 2 for i in com_aspas]}"
        )


def _validar_cpf_vazio(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    if "CPF" not in df.columns:
        return
    vazios = df.index[df["CPF"].replace("", pd.NA).isna()].tolist()
    if vazios:
        resultado.erros.append(
            f"CPF vazio nas linhas: {[i + 2 for i in vazios]}"
        )


def _avisar_cpf_duplicado(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    if "CPF" not in df.columns:
        return
    cpf_validos = df["CPF"].replace("", pd.NA).dropna()
    duplicados = cpf_validos[cpf_validos.duplicated(keep=False)].unique().tolist()
    if duplicados:
        resultado.avisos.append(
            f"CPFs duplicados ({len(duplicados)} CPF(s)): {duplicados[:10]}"
            + (" ..." if len(duplicados) > 10 else "")
        )


def _avisar_nome_vazio(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    if "NOMEPACIENTE" not in df.columns:
        return
    vazios = df.index[df["NOMEPACIENTE"].replace("", pd.NA).isna()].tolist()
    if vazios:
        resultado.avisos.append(
            f"NOMEPACIENTE vazio nas linhas: {[i + 2 for i in vazios]}"
        )


# =============================================================================
# FUNÇÃO PRINCIPAL — genérica
# =============================================================================

def validar(df: pd.DataFrame, config=None) -> ResultadoValidacao:
    """
    Executa validações sobre o DataFrame normalizado.

    Validações genéricas (qualquer config):
        - Colunas obrigatórias presentes e não vazias
        - Aviso se obrigatórias têm células parcialmente vazias

    Validações específicas de PACIENTES (só se as colunas existirem):
        - NOMEPACIENTE sem números ou aspas
        - CPF não vazio
        - Avisos: CPF duplicado, nome vazio

    Args:
        df:     DataFrame normalizado.
        config: Objeto com COLUNAS_OBRIGATORIAS (opcional).
                Se None, usa lista padrão de PACIENTES.
    """
    resultado = ResultadoValidacao()

    # Determina colunas obrigatórias — da config ou padrão PACIENTES
    if config is not None and hasattr(config, "COLUNAS_OBRIGATORIAS"):
        colunas_obrigatorias = config.COLUNAS_OBRIGATORIAS
    else:
        colunas_obrigatorias = ["ID_CLINICA", "NOMEPACIENTE"]

    # Validações genéricas
    _validar_obrigatorios(df, resultado, colunas_obrigatorias)
    _avisar_obrigatorios_parcialmente_vazios(df, resultado, colunas_obrigatorias)

    # Validações específicas de PACIENTES (só disparam se as colunas existirem)
    _validar_nome_paciente(df, resultado)
    _validar_cpf_vazio(df, resultado)
    _avisar_cpf_duplicado(df, resultado)
    _avisar_nome_vazio(df, resultado)

    return resultado
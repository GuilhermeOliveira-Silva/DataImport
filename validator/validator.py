"""
validator/validator.py
Responsabilidade: Validar regras de negócio após a normalização.
Separa erros críticos (bloqueiam execução) de avisos (apenas informam).
"""

import re
import pandas as pd
from dataclasses import dataclass, field


# =============================================================================
# ESTRUTURAS DE RESULTADO
# =============================================================================

@dataclass
class ResultadoValidacao:
    """
    Carrega o resultado completo da validação.

    Atributos:
        erros:  lista de erros críticos — bloqueiam a execução.
        avisos: lista de avisos — não bloqueiam, mas devem ser registrados.
        valido: True somente se não houver nenhum erro crítico.
    """
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
# VALIDAÇÕES CRÍTICAS (bloqueiam execução)
# =============================================================================

def _validar_obrigatorios(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    """ID_CLINICA e NOMEPACIENTE não podem estar ausentes ou todos vazios."""
    for col in ["ID_CLINICA", "NOMEPACIENTE"]:
        if col not in df.columns or df[col].replace("", pd.NA).isna().all():
            resultado.erros.append(
                f"Coluna obrigatória '{col}' está ausente ou completamente vazia."
            )


def _validar_nome_paciente(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    """
    NOMEPACIENTE não pode conter dígitos nem aspas simples.
    Registra o número da linha (1-indexed) para facilitar correção.
    """
    if "NOMEPACIENTE" not in df.columns:
        return

    com_numero = df.index[
        df["NOMEPACIENTE"].fillna("").str.contains(r"\d", regex=True)
    ].tolist()

    com_aspas = df.index[
        df["NOMEPACIENTE"].fillna("").str.contains("'", regex=False)
    ].tolist()

    if com_numero:
        linhas = [i + 2 for i in com_numero]  # +2: cabeçalho + índice 0-based
        resultado.erros.append(
            f"NOMEPACIENTE contém números nas linhas: {linhas}"
        )

    if com_aspas:
        linhas = [i + 2 for i in com_aspas]
        resultado.erros.append(
            f"NOMEPACIENTE contém aspas simples (') nas linhas: {linhas}"
        )


def _validar_cpf_vazio(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    """CPF não pode estar vazio (após normalização)."""
    if "CPF" not in df.columns:
        return

    vazios = df.index[
        df["CPF"].replace("", pd.NA).isna()
    ].tolist()

    if vazios:
        linhas = [i + 2 for i in vazios]
        resultado.erros.append(
            f"CPF vazio nas linhas: {linhas}"
        )


# =============================================================================
# VALIDAÇÕES DE AVISO (não bloqueiam)
# =============================================================================

def _avisar_cpf_duplicado(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    """CPFs que aparecem mais de uma vez geram aviso."""
    if "CPF" not in df.columns:
        return

    cpf_validos = df["CPF"].replace("", pd.NA).dropna()
    duplicados = cpf_validos[cpf_validos.duplicated(keep=False)].unique().tolist()

    if duplicados:
        resultado.avisos.append(
            f"CPFs duplicados encontrados ({len(duplicados)} CPF(s)): {duplicados[:10]}"
            + (" ..." if len(duplicados) > 10 else "")
        )


def _avisar_nome_vazio(df: pd.DataFrame, resultado: ResultadoValidacao) -> None:
    """Linhas com NOMEPACIENTE vazio geram aviso."""
    if "NOMEPACIENTE" not in df.columns:
        return

    vazios = df.index[
        df["NOMEPACIENTE"].replace("", pd.NA).isna()
    ].tolist()

    if vazios:
        linhas = [i + 2 for i in vazios]
        resultado.avisos.append(
            f"NOMEPACIENTE vazio nas linhas: {linhas}"
        )


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

def validar(df: pd.DataFrame) -> ResultadoValidacao:
    """
    Executa todas as validações sobre o DataFrame normalizado.

    Ordem de execução:
        1. Campos obrigatórios presentes
        2. Regras de NOMEPACIENTE
        3. CPF não vazio
        4. Avisos: CPF duplicado
        5. Avisos: nome vazio

    Returns:
        ResultadoValidacao com listas de erros e avisos preenchidas.
    """
    resultado = ResultadoValidacao()

    # Erros críticos
    _validar_obrigatorios(df, resultado)
    _validar_nome_paciente(df, resultado)
    _validar_cpf_vazio(df, resultado)

    # Avisos
    _avisar_cpf_duplicado(df, resultado)
    _avisar_nome_vazio(df, resultado)

    return resultado
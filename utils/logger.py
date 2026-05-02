"""
utils/logger.py
Responsabilidade: Geração de arquivos de log (erros e avisos) e relatório final.
"""

from pathlib import Path
from validator.validator import ResultadoValidacao


# =============================================================================
# NOMES DOS ARQUIVOS (sem pasta — pasta vem do path_manager)
# =============================================================================

NOME_ERROS  = "erros.txt"
NOME_AVISOS = "avisos.txt"


# =============================================================================
# UTILITÁRIO INTERNO
# =============================================================================

def _escrever_arquivo(caminho: str, linhas: list[str], titulo: str) -> None:
    """Escreve uma lista de mensagens em arquivo texto, uma por linha."""
    Path(caminho).parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(f"{titulo}\n")
        f.write("=" * 60 + "\n\n")
        f.write("\n".join(linhas))
        f.write("\n")


# =============================================================================
# FUNÇÕES PÚBLICAS
# =============================================================================

def salvar_erros(resultado: ResultadoValidacao, pasta: str) -> None:
    """Gera erros.txt dentro da pasta de execução."""
    caminho = str(Path(pasta) / NOME_ERROS)
    _escrever_arquivo(
        caminho=caminho,
        linhas=resultado.erros,
        titulo="ERROS CRÍTICOS — Importação bloqueada",
    )
    print(f"      📄 Erros salvos em: {caminho}")


def salvar_avisos(resultado: ResultadoValidacao, pasta: str) -> None:
    """Gera avisos.txt dentro da pasta de execução."""
    caminho = str(Path(pasta) / NOME_AVISOS)
    _escrever_arquivo(
        caminho=caminho,
        linhas=resultado.avisos,
        titulo="AVISOS — Importação continuou, mas revise os itens abaixo",
    )
    print(f"      📄 Avisos salvos em: {caminho}")


def exibir_relatorio(total_linhas: int, resultado: ResultadoValidacao) -> None:
    """Exibe o relatório final no terminal com totais."""
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL")
    print("=" * 60)
    print(f"  ✔️  Total de linhas processadas : {total_linhas}")
    print(f"  ⚠️  Total de avisos             : {len(resultado.avisos)}")
    print(f"  ❌  Total de erros críticos     : {len(resultado.erros)}")
    print("=" * 60)


def registrar_resultado(total_linhas: int, resultado: ResultadoValidacao, pasta: str) -> None:
    """
    Ponto de entrada do logger. Chamado pelo main.py após a validação.

    Comportamento:
        - Sempre exibe o relatório no terminal
        - Se houver erros  → salva erros.txt  na pasta de execução
        - Se houver avisos → salva avisos.txt na pasta de execução
    """
    exibir_relatorio(total_linhas, resultado)

    if resultado.erros:
        salvar_erros(resultado, pasta)

    if resultado.avisos:
        salvar_avisos(resultado, pasta)


# =============================================================================
# PARTE 5.3 — LOG DE ERRO INESPERADO
# =============================================================================

import traceback

NOME_ERRO_DETALHADO = "erro_detalhado.txt"


def salvar_erro_inesperado(erro: Exception, pasta: str) -> None:
    """
    Salva mensagem amigável + stack trace completo em erro_detalhado.txt.
    Chamado apenas quando ocorre uma exceção não tratada no pipeline.

    Args:
        erro:  A exceção capturada.
        pasta: Pasta de execução (gerada pelo path_manager).
               Se vazia (erro antes de criar a pasta), salva direto em output/.
    """
    pasta_destino = Path(pasta) if pasta else Path("output")
    pasta_destino.mkdir(parents=True, exist_ok=True)

    caminho = str(pasta_destino / NOME_ERRO_DETALHADO)
    stack = traceback.format_exc()

    with open(caminho, "w", encoding="utf-8") as f:
        f.write("ERRO INESPERADO — Detalhes técnicos\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Tipo   : {type(erro).__name__}\n")
        f.write(f"Mensagem: {erro}\n\n")
        f.write("Stack trace:\n")
        f.write("-" * 60 + "\n")
        f.write(stack)

    print(f"      📄 Detalhes técnicos salvos em: {caminho}")
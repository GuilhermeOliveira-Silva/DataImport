"""
main.py
Ponto de entrada do sistema de importação.
Suporta uso via CLI (Parte 5.1) e via API (Parte 6).
"""

import sys
import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from transformer.normalizer import processar_planilha
from transformer.normalizeValores import normalizar
from validator.validator import validar
from generator.sql_generator import gerar_e_salvar
from utils.logger import registrar_resultado, salvar_erro_inesperado
from utils.path_manager import criar_pasta_execucao


# =============================================================================
# RESULTADO DO PIPELINE — estrutura retornada para a API e para o CLI
# =============================================================================

@dataclass
class ResultadoPipeline:
    sucesso: bool
    total_linhas: int = 0
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    caminho_sql: str | None = None
    pasta_execucao: str | None = None
    mensagem_erro_inesperado: str | None = None


# =============================================================================
# PIPELINE REUTILIZÁVEL (usado pela CLI e pela API)
# =============================================================================

def processar_importacao(caminho_arquivo: str, tabela: str = "PACIENTES") -> ResultadoPipeline:
    """
    Executa o pipeline completo de importação e retorna um ResultadoPipeline.
    Não chama sys.exit() — deixa o chamador (CLI ou API) decidir o que fazer.

    Etapas:
        0. Parte 5.2 — cria pasta de output exclusiva para esta execução
        1. Parte 1   — leitura, mapeamento e garantia de schema
        2. Parte 2a  — normalização dos valores
        3. Parte 2b  — validação das regras de negócio
        4. Parte 4   — log de erros/avisos + relatório final
        5. Parte 3   — geração do SQL (somente se não houver erros)
    """
    pasta = criar_pasta_execucao()

    try:
        # ------------------------------------------------------------------
        # PARTE 1 — Mapeamento e schema
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("PARTE 1 — Leitura e mapeamento de colunas")
        print("=" * 60)
        df = processar_planilha(caminho_arquivo)

        # ------------------------------------------------------------------
        # PARTE 2a — Normalização
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("PARTE 2a — Normalização dos dados")
        print("=" * 60)
        df = normalizar(df)
        print("✅ Normalização concluída.")

        # ------------------------------------------------------------------
        # PARTE 2b — Validação
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("PARTE 2b — Validação das regras de negócio")
        print("=" * 60)
        resultado_validacao = validar(df)

        # ------------------------------------------------------------------
        # PARTE 4 — Log e relatório final
        # ------------------------------------------------------------------
        registrar_resultado(
            total_linhas=len(df),
            resultado=resultado_validacao,
            pasta=str(pasta),
        )

        # Erros críticos → não gera SQL
        if not resultado_validacao.valido:
            print("\n🚫 Importação interrompida — SQL não será gerado.")
            return ResultadoPipeline(
                sucesso=False,
                total_linhas=len(df),
                erros=resultado_validacao.erros,
                avisos=resultado_validacao.avisos,
                pasta_execucao=str(pasta),
            )

        # ------------------------------------------------------------------
        # PARTE 3 — Geração do SQL
        # ------------------------------------------------------------------
        print("\n" + "=" * 60)
        print("PARTE 3 — Geração do SQL INSERT")
        print("=" * 60)
        caminho_sql = gerar_e_salvar(df, pasta=str(pasta), tabela=tabela)
        print(f"✅ SQL gerado com sucesso: {caminho_sql}")

        return ResultadoPipeline(
            sucesso=True,
            total_linhas=len(df),
            erros=[],
            avisos=resultado_validacao.avisos,
            caminho_sql=caminho_sql,
            pasta_execucao=str(pasta),
        )

    except Exception as erro:
        print("\n❌ Erro inesperado durante o processamento.")
        salvar_erro_inesperado(erro, pasta=str(pasta))
        return ResultadoPipeline(
            sucesso=False,
            pasta_execucao=str(pasta),
            mensagem_erro_inesperado=str(erro),
        )


# =============================================================================
# PARTE 5.1 — CLI
# =============================================================================

def obter_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Automação de importação de dados — transforma planilhas Excel em SQL.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos de uso:\n"
            "  python main.py --arquivo pacientes.xlsx\n"
            "  python main.py --arquivo data/clientes.xlsx --tabela PACIENTES\n"
        ),
    )
    parser.add_argument("--arquivo", required=True, metavar="CAMINHO",
                        help="Caminho do arquivo Excel (.xlsx). Obrigatório.")
    parser.add_argument("--tabela", default="PACIENTES", metavar="NOME",
                        help="Nome da tabela destino. Padrão: PACIENTES")
    return parser.parse_args()


def validar_argumentos(args: argparse.Namespace) -> None:
    if not os.path.exists(args.arquivo):
        print(f"\n❌ Arquivo não encontrado: '{args.arquivo}'")
        sys.exit(1)
    if not args.arquivo.lower().endswith(".xlsx"):
        print(f"\n❌ Formato inválido: '{args.arquivo}' — aceita apenas .xlsx")
        sys.exit(1)


if __name__ == "__main__":
    args = obter_argumentos()
    validar_argumentos(args)

    print(f"\n📂 Arquivo : {args.arquivo}")
    print(f"🗄️  Tabela  : {args.tabela}\n")

    resultado = processar_importacao(args.arquivo, args.tabela)

    if not resultado.sucesso:
        print(f"\n❌ Pipeline encerrado com erros. Verifique: {resultado.pasta_execucao}")
        sys.exit(1)

    print(f"\n✅ Pipeline concluído! {resultado.total_linhas} registros processados.")
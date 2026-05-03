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
# INTERAÇÃO CLI — ID_CLINICA ausente
# =============================================================================

def solicitar_id_clinica_interativo(df: pd.DataFrame) -> pd.DataFrame | None:
    print("\n" + "=" * 60)
    print("⚠️  ID_CLINICA não foi informado no arquivo.")
    print("=" * 60)
    print("Deseja:")
    print("  1 - Informar um valor para todos os registros")
    print("  2 - Cancelar a execução")

    while True:
        escolha = input("\nEscolha (1 ou 2): ").strip()
        if escolha == "2":
            print("\n🚫 Execução cancelada pelo usuário.")
            return None
        if escolha == "1":
            while True:
                valor = input("Digite o ID_CLINICA: ").strip()
                if valor.isdigit():
                    df["ID_CLINICA"] = valor
                    print(f"✅ ID_CLINICA = {valor} aplicado em todas as {len(df)} linhas.")
                    return df
                print("❌ ID_CLINICA deve ser numérico. Tente novamente.")
        print("❌ Opção inválida. Digite 1 ou 2.")


# =============================================================================
# PIPELINE REUTILIZÁVEL (CLI e API)
# =============================================================================

def processar_importacao(
    caminho_arquivo: str,
    tabela: str = "PACIENTES",
    modo_interativo: bool = False,
    id_clinica_fixo: str | None = None,   # ← API passa o valor direto aqui
) -> ResultadoPipeline:
    """
    Args:
        caminho_arquivo:  Caminho do .xlsx
        tabela:           Nome da tabela destino
        modo_interativo:  True = CLI (usa input()) | False = API
        id_clinica_fixo:  Valor fixo de ID_CLINICA enviado pelo front/API
    """
    pasta = criar_pasta_execucao()

    print("\n" + "=" * 60)
    print("PARTE 1 — Leitura e mapeamento de colunas")
    print("=" * 60)

    try:
        df = processar_planilha(caminho_arquivo)

    except ValueError as erro_planilha:
        mensagem = str(erro_planilha)

        if "ID_CLINICA" not in mensagem:
            # Outro erro de validação
            salvar_erro_inesperado(erro_planilha, pasta=str(pasta))
            return ResultadoPipeline(
                sucesso=False,
                pasta_execucao=str(pasta),
                mensagem_erro_inesperado=mensagem,
            )

        # ID_CLINICA ausente — reprocessa sem validar essa coluna
        df = processar_planilha(caminho_arquivo, ignorar_obrigatorias=["ID_CLINICA"])

        if id_clinica_fixo:
            # API: valor veio do front
            df["ID_CLINICA"] = id_clinica_fixo
            print(f"✅ ID_CLINICA = {id_clinica_fixo} aplicado via API.")

        elif modo_interativo:
            # CLI: pergunta ao usuário
            df = solicitar_id_clinica_interativo(df)
            if df is None:
                return ResultadoPipeline(sucesso=False, pasta_execucao=str(pasta))

        else:
            # API sem valor → devolve erro especial para o front perguntar
            return ResultadoPipeline(
                sucesso=False,
                pasta_execucao=str(pasta),
                mensagem_erro_inesperado=mensagem,  # contém "ID_CLINICA" → app.py detecta
            )

    except Exception as erro:
        print("\n❌ Erro inesperado durante o processamento.")
        salvar_erro_inesperado(erro, pasta=str(pasta))
        return ResultadoPipeline(
            sucesso=False,
            pasta_execucao=str(pasta),
            mensagem_erro_inesperado=str(erro),
        )

    try:
        # PARTE 2a — Normalização
        print("\n" + "=" * 60)
        print("PARTE 2a — Normalização dos dados")
        print("=" * 60)
        df = normalizar(df)
        print("✅ Normalização concluída.")

        # PARTE 2b — Validação
        print("\n" + "=" * 60)
        print("PARTE 2b — Validação das regras de negócio")
        print("=" * 60)
        resultado_validacao = validar(df)

        # PARTE 4 — Log e relatório
        registrar_resultado(
            total_linhas=len(df),
            resultado=resultado_validacao,
            pasta=str(pasta),
        )

        if not resultado_validacao.valido:
            print("\n🚫 Importação interrompida — SQL não será gerado.")
            return ResultadoPipeline(
                sucesso=False,
                total_linhas=len(df),
                erros=resultado_validacao.erros,
                avisos=resultado_validacao.avisos,
                pasta_execucao=str(pasta),
            )

        # PARTE 3 — Geração do SQL
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

    resultado = processar_importacao(
        caminho_arquivo=args.arquivo,
        tabela=args.tabela,
        modo_interativo=True,
    )

    if not resultado.sucesso:
        print(f"\n❌ Pipeline encerrado com erros. Verifique: {resultado.pasta_execucao}")
        sys.exit(1)

    print(f"\n✅ Pipeline concluído! {resultado.total_linhas} registros processados.")
"""
main.py
Ponto de entrada do sistema de importação.
Suporta uso via CLI (Parte 5.1) e via API (Parte 6).
"""

import sys
import argparse
import os
from dataclasses import dataclass, field

import pandas as pd

from transformer.normalizer import processar_planilha
from transformer.normalizeValores import normalizar
from validator.validator import validar
from generator.sql_generator import gerar_e_salvar
from utils.logger import registrar_resultado, salvar_erro_inesperado
from utils.path_manager import criar_pasta_execucao
from configs.loader import carregar_config


# =============================================================================
# RESULTADO DO PIPELINE
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
# INTERAÇÃO CLI — coluna obrigatória ausente
# =============================================================================

def solicitar_coluna_interativo(df: pd.DataFrame, coluna: str) -> pd.DataFrame | None:
    """Pergunta ao usuário um valor fixo para preencher uma coluna vazia."""
    print("\n" + "=" * 60)
    print(f"⚠️  {coluna} não foi informado no arquivo.")
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
                valor = input(f"Digite o valor para {coluna}: ").strip()
                if valor:
                    df[coluna] = valor
                    print(f"✅ {coluna} = {valor} aplicado em todas as {len(df)} linhas.")
                    return df
                print("❌ Valor não pode ser vazio. Tente novamente.")
        print("❌ Opção inválida. Digite 1 ou 2.")


# =============================================================================
# PIPELINE REUTILIZÁVEL (CLI e API)
# =============================================================================

def processar_importacao(
    caminho_arquivo: str,
    tabela: str = "PACIENTES",
    modo_interativo: bool = False,
    id_clinica_fixo: str | None = None,
) -> ResultadoPipeline:
    pasta = criar_pasta_execucao()

    # Carrega config da tabela
    config_nome = tabela.lower()
    try:
        config = carregar_config(config_nome)
    except ValueError:
        config = carregar_config("pacientes")

    # ------------------------------------------------------------------
    # PARTE 1 — Leitura e mapeamento
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("PARTE 1 — Leitura e mapeamento de colunas")
    print("=" * 60)

    try:
        df = processar_planilha(caminho_arquivo, config=config)

    except ValueError as erro_planilha:
        mensagem = str(erro_planilha)

        # Tenta identificar qual coluna obrigatória está faltando
        col_faltando = None
        for col in config.COLUNAS_OBRIGATORIAS:
            if col in mensagem:
                col_faltando = col
                break

        if col_faltando is None:
            salvar_erro_inesperado(erro_planilha, pasta=str(pasta))
            return ResultadoPipeline(
                sucesso=False,
                pasta_execucao=str(pasta),
                mensagem_erro_inesperado=mensagem,
            )

        # Reprocessa ignorando a coluna faltante
        df = processar_planilha(
            caminho_arquivo,
            config=config,
            ignorar_obrigatorias=[col_faltando],
        )

        # ID_CLINICA tem tratamento especial via API
        if col_faltando == "ID_CLINICA" and id_clinica_fixo:
            df["ID_CLINICA"] = id_clinica_fixo
            print(f"✅ ID_CLINICA = {id_clinica_fixo} aplicado via API.")
        elif col_faltando == "ID_CLINICA" and not modo_interativo:
            return ResultadoPipeline(
                sucesso=False,
                pasta_execucao=str(pasta),
                mensagem_erro_inesperado=mensagem,
            )
        elif modo_interativo:
            df = solicitar_coluna_interativo(df, col_faltando)
            if df is None:
                return ResultadoPipeline(sucesso=False, pasta_execucao=str(pasta))
        else:
            return ResultadoPipeline(
                sucesso=False,
                pasta_execucao=str(pasta),
                mensagem_erro_inesperado=mensagem,
            )

    except Exception as erro:
        print("\n❌ Erro inesperado durante o processamento.")
        salvar_erro_inesperado(erro, pasta=str(pasta))
        return ResultadoPipeline(
            sucesso=False,
            pasta_execucao=str(pasta),
            mensagem_erro_inesperado=str(erro),
        )

    # ------------------------------------------------------------------
    # PARTES 2, 3 e 4
    # ------------------------------------------------------------------
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
        resultado_validacao = validar(df, config=config)

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
# CLI
# =============================================================================

def obter_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="Automação de importação de dados — transforma planilhas Excel em SQL.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Exemplos de uso:\n"
            "  python main.py --arquivo pacientes.xlsx\n"
            "  python main.py --arquivo agendamentos.xlsx --tabela AGENDAMENTOS\n"
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
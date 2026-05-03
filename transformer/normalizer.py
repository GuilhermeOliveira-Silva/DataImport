"""
transformer/normalizer.py
Responsabilidade: Leitura do Excel, mapeamento de colunas e normalização dos dados.
Motor genérico — configuração vem de configs/*.py via carregar_config().
"""

import re
import pandas as pd
import unicodedata

from configs.pacientes import COLUNAS_BANCO, MAPA_COLUNAS, COLUNAS_OBRIGATORIAS
from configs.loader import carregar_config


# =============================================================================
# 1. SANITIZAÇÃO DE NULOS
# =============================================================================

_STRINGS_NULAS = {"", "nan", "none", "null", "na", "<na>", "n/a", "nd", "-", "nat"}

_LOG_ATUAL: dict | None = None


def _definir_log(log: dict | None) -> None:
    global _LOG_ATUAL
    _LOG_ATUAL = log


def _limpar_log() -> None:
    global _LOG_ATUAL
    _LOG_ATUAL = None


def _inc_log(chave: str, quantidade: int = 1) -> None:
    if _LOG_ATUAL is not None:
        _LOG_ATUAL[chave] = _LOG_ATUAL.get(chave, 0) + quantidade


def para_none(valor):
    """Converte qualquer representação de nulo para None puro."""
    if valor is None:
        return None
    try:
        if pd.isna(valor):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(valor, str) and valor.strip().lower() in _STRINGS_NULAS:
        return None
    return valor


# =============================================================================
# 2. NORMALIZADORES DE CAMPO
# =============================================================================

def normalizar_status(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    mapa = {
        "1": "1", "ativo": "1", "ativa": "1", "a": "1",
        "sim": "1", "s": "1", "true": "1",
        "0": "0", "inativo": "0", "inativa": "0", "i": "0",
        "nao": "0", "não": "0", "n": "0", "false": "0",
    }
    return mapa.get(str(valor).strip().lower(), None)


def normalizar_nome(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        _inc_log("nomes_vazios")
        return None
    texto = str(valor).strip()
    if texto == "":
        _inc_log("nomes_vazios")
        return None
    return texto


def normalizar_cpf(valor) -> str | None:
    valor = para_none(valor)
    original = "" if valor is None else str(valor)
    if valor is None:
        resultado = "00000000000"
        if original.strip() != resultado:
            _inc_log("cpf_ajustados")
        return resultado
    texto = re.sub(r"\D", "", str(valor))
    if texto == "":
        resultado = "00000000000"
        if original.strip() != resultado:
            _inc_log("cpf_ajustados")
        return resultado
    texto = texto[:11]
    resultado = texto.zfill(11)
    if original.strip() != resultado:
        _inc_log("cpf_ajustados")
    return resultado


def normalizar_cpfResponsavel(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    texto = re.sub(r"\D", "", str(valor))
    if texto == "":
        return None
    return texto[:11].zfill(11)


def normalizar_telefone(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    original = str(valor).strip()
    resultado = re.sub(r"\D", "", str(valor))
    resultado_final = resultado if resultado else None
    if resultado_final is not None and original != resultado:
        _inc_log("telefones_formatados")
    return resultado_final


def normalizar_data(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    try:
        return pd.to_datetime(str(valor), dayfirst=True, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return None


def normalizar_sexo(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    mapa = {"m": "M", "masculino": "M", "f": "F", "feminino": "F"}
    return mapa.get(str(valor).strip().lower(), str(valor).strip()) or None


def normalizar_string(valor) -> str | None:
    valor = para_none(valor)
    if valor is None:
        return None
    resultado = str(valor).strip()
    return resultado if resultado else None


def _resolver_normalizador(func):
    """Aceita função direta ou nome de função como string."""
    if callable(func):
        return func
    if isinstance(func, str):
        resolved = globals().get(func)
        if resolved is None:
            raise ValueError(f"Normalizador '{func}' não encontrado no normalizer.")
        return resolved
    raise ValueError("Normalizador inválido — use função ou nome da função.")


# =============================================================================
# 3. FUNÇÕES AUXILIARES DE MAPEAMENTO
# =============================================================================

def normalizar_nome_coluna(nome: str) -> str:
    nome = unicodedata.normalize("NFKD", str(nome))
    nome = nome.encode("ascii", "ignore").decode("ascii")
    # 2. Lowercase
    nome = nome.strip().lower()
    # 3. Substitui caracteres não alfanuméricos por _
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    # 4. Colapsa underscores duplos
    nome = re.sub(r"_+", "_", nome)
    return nome.strip("_")


def detectar_colunas_telefone(
    colunas_normalizadas: list[str],
    mapa_colunas: dict[str, str],
) -> list[str]:
    ja_mapeadas = set(mapa_colunas.keys())
    padrao = re.compile(r"^(tel|fone|telefone|phone)\d*$")
    return [c for c in colunas_normalizadas if padrao.match(c) and c not in ja_mapeadas]


def detectar_colunas_obs(colunas_normalizadas: list[str]) -> list[str]:
    padrao = re.compile(r"^(obs|observa[çc][aã]o|observacao|anotacao|nota)\d+$")
    return [c for c in colunas_normalizadas if padrao.match(c)]


# =============================================================================
# 4. MOTOR PRINCIPAL
# =============================================================================

def processar_planilha(
    caminho_arquivo: str,
    config=None,
    ignorar_obrigatorias: list[str] | None = None,
    log: dict | None = None,
    modo_interativo: bool = True,
    modo_execucao: str = "execucao",
) -> pd.DataFrame:
    """
    Lê o Excel, mapeia colunas para o padrão do banco e retorna DataFrame.

    Args:
        caminho_arquivo:      Caminho do arquivo .xlsx
        config:               Módulo de configuração (padrão: pacientes).
                              Deve expor COLUNAS_BANCO, MAPA_COLUNAS,
                              COLUNAS_OBRIGATORIAS e opcionalmente NORMALIZADORES.
        ignorar_obrigatorias: Colunas obrigatórias a ignorar na validação.
        log:                  Dicionário para acumular métricas de normalização.
        modo_interativo:     Se True, exibe mensagens de progresso e interação.
        modo_execucao:       Modo de execução ("execucao" ou "debug").
    """
    if config is None:
        config = carregar_config("pacientes")

    _definir_log(log)

    try:
        # ETAPA 1 — Leitura
        print(f"[1/5] Lendo arquivo: {caminho_arquivo}")
        df = pd.read_excel(caminho_arquivo, dtype=str)
        print(f"      {len(df)} linhas | {len(df.columns)} colunas encontradas")
        print(f"      Colunas originais: {list(df.columns)}")

        # ETAPA 2 — Normalização interna dos nomes de coluna
        print("\n[2/5] Normalizando nomes de colunas internamente...")
        df_norm = df.rename(columns={col: normalizar_nome_coluna(col) for col in df.columns})
        print(f"      Colunas normalizadas: {list(df_norm.columns)}")

        # ETAPA 3 — Mapeamento para colunas do banco
        print("\n[3/5] Mapeando colunas para o padrão do banco...")
        mapa_final = {}

        for col_norm in df_norm.columns:
            if col_norm in config.MAPA_COLUNAS:
                mapa_final[col_norm] = config.MAPA_COLUNAS[col_norm]

        # Telefones genéricos
        for col_tel in detectar_colunas_telefone(list(df_norm.columns), config.MAPA_COLUNAS):
            for slot in ["CELULAR", "NRO_FONE1", "NRO_FONE2"]:
                if slot not in mapa_final.values():
                    mapa_final[col_tel] = slot
                    print(f"      Telefone genérico '{col_tel}' → {slot}")
                    break
            else:
                print(f"      AVISO: '{col_tel}' ignorado — slots de telefone preenchidos.")

        # Observações extras → concatena
        obs_extras = detectar_colunas_obs(list(df_norm.columns))
        col_obs_principal = next(
            (c for c in df_norm.columns if config.MAPA_COLUNAS.get(c) == "OBSERVACAO"), None
        )
        if obs_extras:
            print(f"      Observações extras: {obs_extras} → concatenadas em OBSERVACAO")
            todas_obs = ([col_obs_principal] if col_obs_principal else []) + obs_extras
            df_norm["_obs_concatenada"] = (
                df_norm[todas_obs]
                .fillna("")
                .apply(lambda row: " | ".join(v for v in row if str(v).strip()), axis=1)
            )
            df_norm.drop(columns=todas_obs, inplace=True, errors="ignore")
            mapa_final.pop(col_obs_principal, None)
            for c in obs_extras:
                mapa_final.pop(c, None)
            mapa_final["_obs_concatenada"] = "OBSERVACAO"

        df_banco = df_norm.rename(columns=mapa_final)
        df_banco = df_banco[[c for c in df_banco.columns if c in config.COLUNAS_BANCO]]
        print(f"      Colunas mapeadas: {list(df_banco.columns)}")

        # ETAPA 4 — Garantir schema fixo (colunas faltantes → None)
        print("\n[4/5] Garantindo todas as colunas do banco...")
        faltantes = [c for c in config.COLUNAS_BANCO if c not in df_banco.columns]
        if faltantes:
            print(f"      Colunas ausentes criadas com NULL: {faltantes}")
        for col in faltantes:
            df_banco[col] = None
        df_banco = df_banco[config.COLUNAS_BANCO]

        # ETAPA 4b — Sanitiza nulos e aplica normalizadores por campo
        df_banco = df_banco.map(para_none)

        normalizadores = getattr(config, "NORMALIZADORES", None)
        if normalizadores:
            # Usa normalizadores declarados na config
            for col, func in normalizadores.items():
                if col not in df_banco.columns:
                    continue
                df_banco[col] = df_banco[col].apply(_resolver_normalizador(func))
        else:
            # Fallback: normalizadores padrão de PACIENTES
            df_banco["STATUS"]               = df_banco["STATUS"].apply(normalizar_status)
            df_banco["NOMEPACIENTE"]         = df_banco["NOMEPACIENTE"].apply(normalizar_nome)
            df_banco["NOME_RESPONSAVEL"]     = df_banco["NOME_RESPONSAVEL"].apply(normalizar_nome)
            df_banco["CPF"]                  = df_banco["CPF"].apply(normalizar_cpf)
            df_banco["CPF_RESPONSAVEL"]      = df_banco["CPF_RESPONSAVEL"].apply(normalizar_cpfResponsavel)
            df_banco["CELULAR"]              = df_banco["CELULAR"].apply(normalizar_telefone)
            df_banco["NRO_FONE1"]            = df_banco["NRO_FONE1"].apply(normalizar_telefone)
            df_banco["NRO_FONE2"]            = df_banco["NRO_FONE2"].apply(normalizar_telefone)
            df_banco["DATA_NASCIMENTO"]      = df_banco["DATA_NASCIMENTO"].apply(normalizar_data)
            df_banco["DATA_CRIACAO"]         = df_banco["DATA_CRIACAO"].apply(normalizar_data)
            df_banco["DATA_ALTERACAO"]       = df_banco["DATA_ALTERACAO"].apply(normalizar_data)
            df_banco["DATA_ULT_ATENDIMENTO"] = df_banco["DATA_ULT_ATENDIMENTO"].apply(normalizar_data)
            df_banco["SEXO"]                 = df_banco["SEXO"].apply(normalizar_sexo)

            cols_string = [
                "RG", "NUMEROFICHA", "EMAIL",
                "LOGRADOURO", "NUMERO", "COMPLEMENTO",
                "BAIRRO", "CIDADE", "ESTADO", "CEP",
                "OBSERVACAO", "PROFISSAO",
            ]
            for col in cols_string:
                df_banco[col] = df_banco[col].apply(normalizar_string)

        # PÓS-PROCESSAMENTO — lógica row-level opcional
        pos_processador = getattr(config, "POS_PROCESSADOR", None)
        if pos_processador is not None:
            df_banco = pos_processador(df_banco)
            print("      ✅ Pós-processamento aplicado.")

        # ETAPA 5 — Validação das colunas obrigatórias
        print("\n[5/5] Validando colunas obrigatórias...")
        colunas_a_validar = [
            col for col in config.COLUNAS_OBRIGATORIAS
            if not (ignorar_obrigatorias and col in ignorar_obrigatorias)
        ]
        erros = [
            col for col in colunas_a_validar
            if df_banco[col].isna().all()
        ]
        if erros:
            raise ValueError(
                f"ERRO: Colunas obrigatórias ausentes ou completamente vazias: {erros}\n"
                "Verifique o arquivo de origem e tente novamente."
            )

        print(f"      OK — colunas obrigatórias presentes: {config.COLUNAS_OBRIGATORIAS}")
        print(f"\n✅ Processamento concluído! {df_banco.shape[0]} linhas × {df_banco.shape[1]} colunas")
        return df_banco

    finally:
        _limpar_log()


# =============================================================================
# EXECUÇÃO DIRETA
# =============================================================================

if __name__ == "__main__":
    import sys

    caminho = sys.argv[1] if len(sys.argv) > 1 else "planilha_cliente.xlsx"

    try:
        df_resultado = processar_planilha(caminho)
        print("\n--- Prévia (5 primeiras linhas) ---")
        print(df_resultado.head().to_string(index=False))
        saida = "dados_normalizados.xlsx"
        df_resultado.to_excel(saida, index=False)
        print(f"\n💾 Salvo em: {saida}")
    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Arquivo '{caminho}' não encontrado.")
        sys.exit(1)
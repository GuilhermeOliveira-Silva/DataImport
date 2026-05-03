"""
transformer/normalizer.py
Responsabilidade: Leitura do Excel, mapeamento de colunas e normalização dos dados.
"""

import re
import pandas as pd


# =============================================================================
# 1. DEFINIÇÃO DO PADRÃO DO BANCO
# =============================================================================

COLUNAS_OBRIGATORIAS = ["ID_CLINICA"]

COLUNAS_BANCO = [
    "ID_CLINICA",
    "STATUS",
    "NOMEPACIENTE",
    "CPF",
    "RG",
    "NUMEROFICHA",
    "DATA_NASCIMENTO",
    "EMAIL",
    "CELULAR",
    "NRO_FONE1",
    "NRO_FONE2",
    "OBSERVACAO",
    "LOGRADOURO",
    "NUMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CIDADE",
    "ESTADO",
    "CEP",
    "SEXO",
    "DATA_CRIACAO",
    "DATA_ALTERACAO",
    "NOME_RESPONSAVEL",
    "CPF_RESPONSAVEL",
    "DATA_ULT_ATENDIMENTO",
    "PROFISSAO",
]

MAPA_COLUNAS = {
    # =========================
    # ID_CLINICA
    # =========================
    "id_clinica": "ID_CLINICA",
    "clinica": "ID_CLINICA",
    "cod_clinica": "ID_CLINICA",
    "codigo_clinica": "ID_CLINICA",

    # =========================
    # STATUS
    # =========================
    "status": "STATUS",
    "situacao": "STATUS",
    "ativo": "STATUS",

    # =========================
    # PACIENTE
    # =========================
    "nomepaciente": "NOMEPACIENTE",
    "nome_paciente": "NOMEPACIENTE",
    "nome": "NOMEPACIENTE",
    "paciente": "NOMEPACIENTE",
    "nome_completo": "NOMEPACIENTE",

    # =========================
    # DOCUMENTOS
    # =========================
    "cpf": "CPF",
    "nr_cpf": "CPF",
    "nro_cpf": "CPF",
    "documento": "CPF",

    "rg": "RG",
    "registro_geral": "RG",

    # =========================
    # FICHA / CÓDIGO
    # =========================
    "numeroficha": "NUMEROFICHA",
    "numero_ficha": "NUMEROFICHA",
    "ficha": "NUMEROFICHA",

    # =========================
    # DATA NASCIMENTO
    # =========================
    "data_nascimento": "DATA_NASCIMENTO",
    "DATADENASCIMENTO": "DATA_NASCIMENTO",
    "DATA_NASC": "DATA_NASCIMENTO",
    "nascimento": "DATA_NASCIMENTO",
    "data_nasc": "DATA_NASCIMENTO",
    "dt_nasc": "DATA_NASCIMENTO",

    # =========================
    # CONTATO
    # =========================
    "email": "EMAIL",
    "e_mail": "EMAIL",
    "mail": "EMAIL",
    "correio_eletronico": "EMAIL",

    "celular": "CELULAR",
    "nro_celular": "CELULAR",
    "cel": "CELULAR",
    "telefone_celular": "CELULAR",
    "whatsapp": "CELULAR",

    "nro_fone1": "NRO_FONE1",
    "fone1": "NRO_FONE1",
    "telefone1": "NRO_FONE1",
    "tel1": "NRO_FONE1",
    "fone_residencial": "NRO_FONE1",
    "telefone_residencial": "NRO_FONE1",

    "nro_fone2": "NRO_FONE2",
    "fone2": "NRO_FONE2",
    "telefone2": "NRO_FONE2",
    "tel2": "NRO_FONE2",
    "fone_comercial": "NRO_FONE2",
    "telefone_comercial": "NRO_FONE2",

    # =========================
    # ENDEREÇO
    # =========================
    "logradouro": "LOGRADOURO",
    "rua": "LOGRADOURO",
    "av": "LOGRADOURO",
    "avenida": "LOGRADOURO",
    "end": "LOGRADOURO",

    "numero": "NUMERO",
    "nro": "NUMERO",
    "num": "NUMERO",
    "nr": "NUMERO",

    "complemento": "COMPLEMENTO",
    "comp": "COMPLEMENTO",

    "bairro": "BAIRRO",
    "bairro_residencial": "BAIRRO",

    "cidade": "CIDADE",
    "municipio": "CIDADE",

    "estado": "ESTADO",
    "uf": "ESTADO",
    "sigla_estado": "ESTADO",

    "cep": "CEP",
    "cod_postal": "CEP",

    # =========================
    # OUTROS CAMPOS
    # =========================
    "sexo": "SEXO",
    "genero": "SEXO",
    "gender": "SEXO",

    "observacao": "OBSERVACAO",
    "obs": "OBSERVACAO",
    "observacoes": "OBSERVACAO",
    "anotacao": "OBSERVACAO",
    "anotacoes": "OBSERVACAO",
    "nota": "OBSERVACAO",
    "notas": "OBSERVACAO",

    # =========================
    # CONTROLE DE SISTEMA
    # =========================
    "data_criacao": "DATA_CRIACAO",
    "data_alteracao": "DATA_ALTERACAO",
    "data_ult_atendimento": "DATA_ULT_ATENDIMENTO",

    "nome_responsavel": "NOME_RESPONSAVEL",
    "cpf_responsavel": "CPF_RESPONSAVEL",

    "profissao": "PROFISSAO",
}


# =============================================================================
# 2. SANITIZAÇÃO DE NULOS
# Garante que pd.NA / NaN / "<NA>" / strings vazias virem None puro,
# que é o único valor convertido corretamente para NULL pelo sql_generator.
# =============================================================================

_STRINGS_NULAS = {"", "nan", "none", "null", "na", "<na>", "n/a", "nd", "-", "nat"}


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
# 3. NORMALIZADORES DE CAMPO
# =============================================================================

def normalizar_status(valor) -> str | None:
    """
    Converte STATUS para '1' (ativo) ou '0' (inativo).

    Aceita:
        '1' / 'ativo' / 'ativa' / 'a' / 'sim' / 's' / 'true'   → '1'
        '0' / 'inativo' / 'inativa' / 'i' / 'nao' / 'n' / 'false' → '0'
        None / vazio → None (NULL no SQL)
    """
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
    """Converte nome vazio ou nulo para None."""
    valor = para_none(valor)
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto == "" else texto


def normalizar_cpf(valor) -> str | None:
    """
    Remove não-numéricos e completa com zeros à esquerda até 11 dígitos.
    CPF vazio ou nulo → '00000000000'.
    """
    valor = para_none(valor)
    if valor is None:
        return "00000000000"
    texto = re.sub(r"\D", "", str(valor))
    if texto == "":
        return "00000000000"
    texto = texto[:11]
    return texto.zfill(11)


def normalizar_cpfResponsavel(valor) -> str | None:
    """
    Remove não-numéricos e completa com zeros à esquerda até 11 dígitos.
    CPF do responsável vazio ou nulo → None (NULL no SQL).
    """
    valor = para_none(valor)
    if valor is None:
        return None
    texto = re.sub(r"\D", "", str(valor))
    if texto == "":
        return None
    texto = texto[:11]
    return texto.zfill(11)


def normalizar_telefone(valor) -> str | None:
    """Remove tudo que não for dígito. Vazio → None."""
    valor = para_none(valor)
    if valor is None:
        return None
    resultado = re.sub(r"\D", "", str(valor))
    return resultado if resultado else None


def normalizar_data(valor) -> str | None:
    """
    Converte datas variadas para YYYY-MM-DD.
    Retorna None se não conseguir converter (vai virar NULL no SQL).
    """
    valor = para_none(valor)
    if valor is None:
        return None
    try:
        return pd.to_datetime(str(valor), dayfirst=True, errors="raise").strftime("%Y-%m-%d")
    except Exception:
        return None


def normalizar_sexo(valor) -> str | None:
    """Masculino/M → 'M', Feminino/F → 'F', outros → None."""
    valor = para_none(valor)
    if valor is None:
        return None
    mapa = {
        "m": "M", "masculino": "M",
        "f": "F", "feminino": "F",
    }
    return mapa.get(str(valor).strip().lower(), str(valor).strip()) or None


def normalizar_string(valor) -> str | None:
    """Strip e vazio → None."""
    valor = para_none(valor)
    if valor is None:
        return None
    resultado = str(valor).strip()
    return resultado if resultado else None


# =============================================================================
# 4. FUNÇÕES AUXILIARES DE MAPEAMENTO
# =============================================================================

def normalizar_nome_coluna(nome: str) -> str:
    nome = str(nome).strip().lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)
    nome = re.sub(r"_+", "_", nome)
    return nome.strip("_")


def detectar_colunas_telefone(colunas_normalizadas: list[str]) -> list[str]:
    ja_mapeadas = set(MAPA_COLUNAS.keys())
    padrao = re.compile(r"^(tel|fone|telefone|phone)\d*$")
    return [c for c in colunas_normalizadas if padrao.match(c) and c not in ja_mapeadas]


def detectar_colunas_obs(colunas_normalizadas: list[str]) -> list[str]:
    padrao = re.compile(r"^(obs|observa[çc][aã]o|observacao|anotacao|nota)\d+$")
    return [c for c in colunas_normalizadas if padrao.match(c)]


# =============================================================================
# 5. LEITURA E MAPEAMENTO DO EXCEL
# =============================================================================

def processar_planilha(caminho_arquivo: str, ignorar_obrigatorias: list[str] | None = None) -> pd.DataFrame:
    """
    Lê o Excel, mapeia colunas para o padrão do banco e retorna DataFrame.
    """

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
        if col_norm in MAPA_COLUNAS:
            mapa_final[col_norm] = MAPA_COLUNAS[col_norm]

    # Telefones genéricos
    for col_tel in detectar_colunas_telefone(list(df_norm.columns)):
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
        (c for c in df_norm.columns if MAPA_COLUNAS.get(c) == "OBSERVACAO"), None
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
    df_banco = df_banco[[c for c in df_banco.columns if c in COLUNAS_BANCO]]
    print(f"      Colunas mapeadas: {list(df_banco.columns)}")

    # ETAPA 4 — Garantir schema fixo (colunas faltantes → None)
    print("\n[4/5] Garantindo todas as colunas do banco...")
    faltantes = [c for c in COLUNAS_BANCO if c not in df_banco.columns]
    if faltantes:
        print(f"      Colunas ausentes criadas com NULL: {faltantes}")
    for col in faltantes:
        df_banco[col] = None
    df_banco = df_banco[COLUNAS_BANCO]  # ordem fixa

    # ETAPA 4b — Sanitiza nulos e aplica normalizadores por campo
    df_banco = df_banco.map(para_none)

    # Campos com normalização específica
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

    # Campos de texto simples
    cols_string = [
        "RG", "NUMEROFICHA", "EMAIL",
        "LOGRADOURO", "NUMERO", "COMPLEMENTO",
        "BAIRRO", "CIDADE", "ESTADO", "CEP",
        "OBSERVACAO", "PROFISSAO",
    ]
    for col in cols_string:
        df_banco[col] = df_banco[col].apply(normalizar_string)

    # ETAPA 5 — Validação das colunas obrigatórias
    print("\n[5/5] Validando colunas obrigatórias...")
    colunas_a_validar = [
        col for col in COLUNAS_OBRIGATORIAS
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

    print(f"      OK — colunas obrigatórias presentes: {COLUNAS_OBRIGATORIAS}")
    print(f"\n✅ Processamento concluído! {df_banco.shape[0]} linhas × {df_banco.shape[1]} colunas")
    return df_banco


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
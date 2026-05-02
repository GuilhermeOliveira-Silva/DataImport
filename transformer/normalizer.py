import re
import pandas as pd


# =============================================================================
# 1. DEFINIÇÃO DO PADRÃO DO BANCO
# =============================================================================

# Colunas obrigatórias — o processo para se alguma estiver ausente nos dados
COLUNAS_OBRIGATORIAS = ["ID_CLINICA"]

# Todas as colunas da tabela destino (ordem e grafia exatas do banco)
COLUNAS_BANCO = [
    "ID_CLINICA",
    "NOMEPACIENTE",
    "CPF",
    "DT_NASCIMENTO",
    "SEXO",
    "EMAIL",
    "NRO_CELULAR",
    "NRO_FONE1",
    "NRO_FONE2",
    "ENDERECO",
    "NUMERO",
    "COMPLEMENTO",
    "BAIRRO",
    "CIDADE",
    "ESTADO",
    "CEP",
    "OBSERVACAO",
]


# =============================================================================
# 2. MAPEAMENTO DE SINÔNIMOS
# Chave  → nome normalizado interno usado para identificar a coluna do cliente
# Valor  → nome oficial da coluna no banco (maiúsculo, sem alteração)
# =============================================================================

MAPA_COLUNAS = {
    # Identificador da clínica
    "id_clinica": "ID_CLINICA",
    "clinica": "ID_CLINICA",
    "cod_clinica": "ID_CLINICA",
    "codigo_clinica": "ID_CLINICA",

    # Nome do paciente
    "nomepaciente": "NOMEPACIENTE",
    "nome_paciente": "NOMEPACIENTE",
    "nome": "NOMEPACIENTE",
    "paciente": "NOMEPACIENTE",
    "nome_completo": "NOMEPACIENTE",

    # CPF
    "cpf": "CPF",
    "nr_cpf": "CPF",
    "nro_cpf": "CPF",
    "documento": "CPF",

    # Data de nascimento
    "dt_nascimento": "DT_NASCIMENTO",
    "data_nascimento": "DT_NASCIMENTO",
    "nascimento": "DT_NASCIMENTO",
    "data_nasc": "DT_NASCIMENTO",
    "dt_nasc": "DT_NASCIMENTO",

    # Sexo
    "sexo": "SEXO",
    "genero": "SEXO",
    "gender": "SEXO",

    # E-mail
    "email": "EMAIL",
    "e_mail": "EMAIL",
    "mail": "EMAIL",
    "correio_eletronico": "EMAIL",

    # Telefones
    "nro_celular": "NRO_CELULAR",
    "celular": "NRO_CELULAR",
    "cel": "NRO_CELULAR",
    "fone_celular": "NRO_CELULAR",
    "telefone_celular": "NRO_CELULAR",
    "whatsapp": "NRO_CELULAR",

    "nro_fone1": "NRO_FONE1",
    "fone1": "NRO_FONE1",
    "telefone1": "NRO_FONE1",
    "tel1": "NRO_FONE1",
    "fone_residencial": "NRO_FONE1",
    "telefone_residencial": "NRO_FONE1",
    "residencial": "NRO_FONE1",

    "nro_fone2": "NRO_FONE2",
    "fone2": "NRO_FONE2",
    "telefone2": "NRO_FONE2",
    "tel2": "NRO_FONE2",
    "fone_comercial": "NRO_FONE2",
    "telefone_comercial": "NRO_FONE2",
    "comercial": "NRO_FONE2",

    # Endereço
    "endereco": "ENDERECO",
    "logradouro": "ENDERECO",
    "rua": "ENDERECO",
    "av": "ENDERECO",
    "avenida": "ENDERECO",
    "end": "ENDERECO",

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

    # Observações
    "observacao": "OBSERVACAO",
    "obs": "OBSERVACAO",
    "observacoes": "OBSERVACAO",
    "anotacao": "OBSERVACAO",
    "anotacoes": "OBSERVACAO",
    "nota": "OBSERVACAO",
    "notas": "OBSERVACAO",
}


# =============================================================================
# 3. FUNÇÕES AUXILIARES
# =============================================================================

def normalizar_nome_coluna(nome: str) -> str:
    """
    Converte um nome de coluna qualquer para um formato interno padronizado.
    Usado APENAS para identificação — nunca aparece no output final.

    Exemplos:
        "Nome Paciente" → "nome_paciente"
        "NRO. CELULAR"  → "nro_celular"
        "Fone 1"        → "fone_1"   (depois tratado como "fone1" via mapa)
    """
    nome = str(nome).strip().lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome)   # substitui caracteres especiais por _
    nome = re.sub(r"_+", "_", nome)            # colapsa underscores duplos
    nome = nome.strip("_")
    return nome


def detectar_colunas_telefone(colunas_normalizadas: list[str]) -> list[str]:
    """
    Retorna todas as colunas normalizadas que parecem ser telefones genéricos
    (ex.: "telefone", "fone", "tel") — excluindo as já mapeadas explicitamente.
    """
    ja_mapeadas = set(MAPA_COLUNAS.keys())
    padrao = re.compile(r"^(tel|fone|telefone|phone)\d*$")
    return [c for c in colunas_normalizadas if padrao.match(c) and c not in ja_mapeadas]


def detectar_colunas_obs(colunas_normalizadas: list[str]) -> list[str]:
    """
    Retorna todas as colunas normalizadas que parecem ser observações extras
    (ex.: "obs1", "obs2", "observacao2") — além da OBSERVACAO principal.
    """
    padrao = re.compile(r"^(obs|observa[çc][aã]o|observacao|anotacao|nota)\d+$")
    return [c for c in colunas_normalizadas if padrao.match(c)]


# =============================================================================
# 4. FUNÇÃO PRINCIPAL
# =============================================================================

def processar_planilha(caminho_arquivo: str) -> pd.DataFrame:
    """
    Lê um arquivo Excel do cliente, aplica todas as transformações da Parte 1
    e retorna um DataFrame no padrão do banco.

    Etapas:
        1. Leitura do Excel
        2. Normalização interna dos nomes de coluna
        3. Mapeamento para colunas do banco (incluindo telefones e obs extras)
        4. Garantia de todas as colunas do banco (faltantes → NULL)
        5. Validação das colunas obrigatórias
        6. Retorno do DataFrame no padrão final

    Raises:
        ValueError: se alguma coluna obrigatória estiver ausente nos dados.
    """

    # ------------------------------------------------------------------
    # ETAPA 1 — Leitura do arquivo Excel
    # ------------------------------------------------------------------
    print(f"[1/5] Lendo arquivo: {caminho_arquivo}")
    df = pd.read_excel(caminho_arquivo, dtype=str)  # dtype=str evita conversões automáticas
    print(f"      {len(df)} linhas | {len(df.columns)} colunas encontradas")
    print(f"      Colunas originais: {list(df.columns)}")

    # ------------------------------------------------------------------
    # ETAPA 2 — Normalização interna dos nomes de coluna
    # ------------------------------------------------------------------
    print("\n[2/5] Normalizando nomes de colunas internamente...")

    mapa_original_para_normalizado = {
        col: normalizar_nome_coluna(col) for col in df.columns
    }
    df_norm = df.rename(columns=mapa_original_para_normalizado)

    print(f"      Colunas normalizadas: {list(df_norm.columns)}")

    # ------------------------------------------------------------------
    # ETAPA 3 — Mapeamento para colunas do banco
    # ------------------------------------------------------------------
    print("\n[3/5] Mapeando colunas para o padrão do banco...")

    mapa_final = {}  # normalizado → coluna_banco

    # 3a. Mapeamento direto via dicionário de sinônimos
    for col_norm in df_norm.columns:
        if col_norm in MAPA_COLUNAS:
            mapa_final[col_norm] = MAPA_COLUNAS[col_norm]

    # 3b. Telefones genéricos: primeiro vira CELULAR, depois FONE1, FONE2
    telefones_genericos = detectar_colunas_telefone(list(df_norm.columns))
    slots_telefone = ["NRO_CELULAR", "NRO_FONE1", "NRO_FONE2"]

    for col_tel in telefones_genericos:
        # Só aloca se o slot ainda não foi preenchido por outro mapeamento
        for slot in slots_telefone:
            if slot not in mapa_final.values():
                mapa_final[col_tel] = slot
                print(f"      Telefone genérico '{col_tel}' → {slot}")
                break
        else:
            print(f"      AVISO: '{col_tel}' ignorado — todos os slots de telefone já preenchidos.")

    # 3c. Colunas de observação extras são concatenadas na OBSERVACAO principal
    obs_extras = detectar_colunas_obs(list(df_norm.columns))
    col_obs_principal = next(
        (c for c in df_norm.columns if MAPA_COLUNAS.get(c) == "OBSERVACAO"), None
    )

    if obs_extras:
        print(f"      Observações extras detectadas: {obs_extras} → serão concatenadas em OBSERVACAO")
        todas_obs = ([col_obs_principal] if col_obs_principal else []) + obs_extras

        # Concatena separando por " | ", ignorando células vazias
        df_norm["_obs_concatenada"] = (
            df_norm[todas_obs]
            .fillna("")
            .apply(lambda row: " | ".join(v for v in row if v.strip()), axis=1)
        )

        # Remove colunas originais de obs e usa a concatenada
        df_norm.drop(columns=todas_obs, inplace=True, errors="ignore")
        if col_obs_principal in mapa_final:
            del mapa_final[col_obs_principal]
        for c in obs_extras:
            mapa_final.pop(c, None)

        mapa_final["_obs_concatenada"] = "OBSERVACAO"

    # Renomeia para os nomes do banco
    df_banco = df_norm.rename(columns=mapa_final)

    # Remove colunas que não pertencem ao banco (não mapeadas)
    colunas_validas = [c for c in df_banco.columns if c in COLUNAS_BANCO]
    df_banco = df_banco[colunas_validas]

    print(f"      Colunas mapeadas com sucesso: {list(df_banco.columns)}")

    # ------------------------------------------------------------------
    # ETAPA 4 — Garantir todas as colunas do banco (faltantes → NULL)
    # ------------------------------------------------------------------
    print("\n[4/5] Garantindo todas as colunas do banco...")

    faltantes = [c for c in COLUNAS_BANCO if c not in df_banco.columns]
    if faltantes:
        print(f"      Colunas ausentes preenchidas com NULL: {faltantes}")
    for col in faltantes:
        df_banco[col] = pd.NA

    # Reordena exatamente como o banco espera
    df_banco = df_banco[COLUNAS_BANCO]

    # NORMALIZAÇÃO DE CAMPOS
    if "NOMEPACIENTE" in df_banco.columns:
      df_banco["NOMEPACIENTE"] = df_banco["NOMEPACIENTE"].apply(normalizar_nome)

    if "CPF" in df_banco.columns:
      df_banco["CPF"] = df_banco["CPF"].apply(normalizar_cpf)

    # ------------------------------------------------------------------
    # ETAPA 5 — Validação das colunas obrigatórias
    # ------------------------------------------------------------------
    print("\n[5/5] Validando colunas obrigatórias...")

    erros = []
    for col in COLUNAS_OBRIGATORIAS:
        if col == "NOMEPACIENTE":
            continue
        if df_banco[col].isna().all():
            erros.append(col)

    if erros:
        raise ValueError(
            f"ERRO: As seguintes colunas obrigatórias estão ausentes ou completamente vazias: {erros}\n"
            "Verifique o arquivo de origem e tente novamente."
        )

    print(f"      OK — colunas obrigatórias presentes: {COLUNAS_OBRIGATORIAS}")
    print(f"\n✅ Processamento concluído! DataFrame final: {df_banco.shape[0]} linhas × {df_banco.shape[1]} colunas")

    return df_banco


# =============================================================================
# 5. EXECUÇÃO DE EXEMPLO
# =============================================================================

if __name__ == "__main__":
    import sys

    caminho = sys.argv[1] if len(sys.argv) > 1 else "planilha_cliente.xlsx"

    try:
        df_resultado = processar_planilha(caminho)

        print("\n--- Prévia do resultado (5 primeiras linhas) ---")
        print(df_resultado.head().to_string(index=False))

        saida = "dados_normalizados.xlsx"
        df_resultado.to_excel(saida, index=False)
        print(f"\n💾 Arquivo salvo em: {saida}")

    except ValueError as e:
        print(f"\n❌ {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Arquivo '{caminho}' não encontrado.")
        sys.exit(1)


# =============================================================================
# 5. Normalizador
# =============================================================================
def normalizar_nome(valor: object) -> object:   
    """
    Converte nome vazio ou nulo para None.
    """
    if valor is None:
        return None
    texto = str(valor).strip()
    return None if texto == "" else texto


def normalizar_cpf(valor: object) -> object:
    """
    Remove nao-numericos e completa com zeros a esquerda ate 11 digitos.
    """
    if valor is None:
        return "00000000000"
    texto = re.sub(r"\D", "", str(valor))
    if texto == "":
        return "00000000000"
    
    while len(texto) > 11:
      texto = texto[:-1]
      
    if len(texto) < 11:
        texto = texto.zfill(11)
    return texto
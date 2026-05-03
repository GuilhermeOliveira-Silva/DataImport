"""
configs/pacientes.py
Configuracoes de colunas e mapeamentos para o tipo PACIENTES.
"""

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
    # FICHA / CODIGO
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
    # ENDERECO
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

NORMALIZADORES = {
    "STATUS": "normalizar_status",
    "NOMEPACIENTE": "normalizar_nome",
    "NOME_RESPONSAVEL": "normalizar_nome",
    "CPF": "normalizar_cpf",
    "CPF_RESPONSAVEL": "normalizar_cpfResponsavel",
    "CELULAR": "normalizar_telefone",
    "NRO_FONE1": "normalizar_telefone",
    "NRO_FONE2": "normalizar_telefone",
    "DATA_NASCIMENTO": "normalizar_data",
    "DATA_CRIACAO": "normalizar_data",
    "DATA_ALTERACAO": "normalizar_data",
    "DATA_ULT_ATENDIMENTO": "normalizar_data",
    "SEXO": "normalizar_sexo",
    "RG": "normalizar_string",
    "NUMEROFICHA": "normalizar_string",
    "EMAIL": "normalizar_string",
    "LOGRADOURO": "normalizar_string",
    "NUMERO": "normalizar_string",
    "COMPLEMENTO": "normalizar_string",
    "BAIRRO": "normalizar_string",
    "CIDADE": "normalizar_string",
    "ESTADO": "normalizar_string",
    "CEP": "normalizar_string",
    "OBSERVACAO": "normalizar_string",
    "PROFISSAO": "normalizar_string",
}

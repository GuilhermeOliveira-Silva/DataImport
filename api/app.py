"""
api/app.py
Parte 6 — API FastAPI para upload de planilhas Excel.
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from configs.loader import carregar_config
from generator.sql_generator import gerar_e_salvar
from transformer.normalizer import processar_planilha
from transformer.normalizeValores import normalizar
from utils.logger import registrar_resultado
from utils.path_manager import criar_pasta_execucao
from validator.validator import validar

app = FastAPI(
    title="Data Import API",
    description="Upload de planilhas Excel para geração automática de SQL INSERT.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Avisos", "X-Avisos-Detalhes"],
)


@app.post("/upload")
async def upload_planilha(
    arquivo: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    tabela: str = Form(default="PACIENTES", description="Nome da tabela destino"),
    id_clinica: str = Form(default="", description="ID da clínica (opcional)"),
    tipo_importacao: str = Query(default="pacientes", description="Tipo de importacao"),
    modo_retorno: str = Query(default="preview", description="preview ou arquivo"),
    modo_execucao: str = Query(default="execucao", description="execucao ou validacao"),
):
    if not arquivo.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie um arquivo .xlsx.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
        caminho_tmp = tmp.name

    pasta = criar_pasta_execucao()
    log = {
        "total_registros": 0,
        "cpf_ajustados": 0,
        "nomes_vazios": 0,
        "telefones_formatados": 0,
        "erros": [],
    }

    modo_exec = modo_execucao.strip().lower()
    if modo_exec not in {"execucao", "validacao"}:
        raise HTTPException(status_code=400, detail="modo_execucao invalido. Use 'execucao' ou 'validacao'.")

    try:
        config = carregar_config(tipo_importacao.lower())
        df = processar_planilha(
            caminho_arquivo=caminho_tmp,
            config=config,
            modo_interativo=False,
            modo_execucao=modo_exec,
            log=log,
        )
        df = normalizar(df)

        if tipo_importacao.lower() == "pacientes" and id_clinica.strip():
            df["ID_CLINICA"] = id_clinica.strip()

        if tipo_importacao.lower() == "pacientes":
            resultado_validacao = validar(df)
            registrar_resultado(
                total_linhas=len(df),
                resultado=resultado_validacao,
                pasta=str(pasta),
            )
            if not resultado_validacao.valido:
                return JSONResponse(
                    status_code=422,
                    content={
                        "sucesso": False,
                        "total_linhas": len(df),
                        "erros": resultado_validacao.erros,
                        "avisos": resultado_validacao.avisos,
                        "pasta_execucao": str(pasta),
                    },
                )

        if modo_exec == "execucao":
            caminho_sql = gerar_e_salvar(
                df,
                pasta=str(pasta),
                tabela=tabela or tipo_importacao.upper(),
            )
        else:
            caminho_sql = None
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))
    except Exception as erro:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar o arquivo: {erro}",
        )
    finally:
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

    log["total_registros"] = len(df)
    preview = df.head(5).to_dict(orient="records")

    if modo_exec == "validacao":
        return JSONResponse(
            status_code=200,
            content={
                "status": "validacao",
                "preview": preview,
                "total_registros": len(df),
                "log": log,
            },
        )

    modo = modo_retorno.strip().lower()
    if modo not in {"preview", "arquivo"}:
        raise HTTPException(status_code=400, detail="modo_retorno invalido. Use 'preview' ou 'arquivo'.")

    if modo == "arquivo":
        return FileResponse(
            path=caminho_sql,
            media_type="text/plain",
            filename=f"inserts_{tipo_importacao.lower()}.txt",
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "sucesso",
            "preview": preview,
            "total_registros": len(df),
            "caminho_sql": caminho_sql,
            "log": log,
        },
    )


@app.get("/health")
def health():
    return {"status": "ok"}
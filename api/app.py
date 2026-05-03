"""
api/app.py
Parte 6 — API FastAPI para upload de planilhas Excel.
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from main import processar_importacao

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
):
    if not arquivo.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Formato inválido. Envie um arquivo .xlsx.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
        caminho_tmp = tmp.name

    try:
        resultado = processar_importacao(
            caminho_arquivo=caminho_tmp,
            tabela=tabela,
            modo_interativo=False,
            id_clinica_fixo=id_clinica.strip() or None,
        )
    finally:
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

    # ID_CLINICA ausente → código 461 para o front perguntar
    if resultado.mensagem_erro_inesperado and "ID_CLINICA" in resultado.mensagem_erro_inesperado:
        return JSONResponse(
            status_code=461,
            content={
                "codigo": "ID_CLINICA_AUSENTE",
                "mensagem": "O arquivo não contém ID_CLINICA. Informe o valor para continuar.",
            },
        )

    # Erro inesperado
    if resultado.mensagem_erro_inesperado:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao processar o arquivo. Verifique o formato ou tente novamente. Log salvo em: {resultado.pasta_execucao}",
        )

    # Erros de validação
    if not resultado.sucesso:
        return JSONResponse(
            status_code=422,
            content={
                "sucesso": False,
                "total_linhas": resultado.total_linhas,
                "erros": resultado.erros,
                "avisos": resultado.avisos,
                "pasta_execucao": resultado.pasta_execucao,
            },
        )

    # Sucesso → download do SQL
    headers = {}
    if resultado.avisos:
        headers["X-Avisos"] = str(len(resultado.avisos))
        headers["X-Avisos-Detalhes"] = f"Ver {resultado.pasta_execucao}/avisos.txt"

    return FileResponse(
        path=resultado.caminho_sql,
        media_type="text/plain",
        filename="inserts_pacientes.txt",
        headers=headers,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
"""
api/app.py
Parte 6 — API FastAPI para upload de planilhas Excel.
Reutiliza o pipeline existente via processar_importacao().
"""

import os
import shutil
import tempfile

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from main import processar_importacao


# =============================================================================
# APLICAÇÃO
# =============================================================================

app = FastAPI(
    title="Data Import API",
    description="Upload de planilhas Excel para geração automática de SQL INSERT.",
    version="1.0.0",
)


# =============================================================================
# ENDPOINT PRINCIPAL
# =============================================================================

@app.post("/upload")
async def upload_planilha(
    arquivo: UploadFile = File(..., description="Arquivo Excel (.xlsx)"),
    tabela: str = Form(default="PACIENTES", description="Nome da tabela destino"),
):
    """
    Recebe um arquivo .xlsx, executa o pipeline completo e retorna:

    - **Sucesso sem avisos**   → arquivo .txt com o SQL para download
    - **Sucesso com avisos**   → arquivo .txt com o SQL + avisos no header
    - **Erros de validação**   → JSON com lista de erros (sem SQL)
    - **Erro inesperado**      → HTTP 500 com mensagem amigável
    """

    # ------------------------------------------------------------------
    # 1. Validação básica do arquivo recebido
    # ------------------------------------------------------------------
    if not arquivo.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Formato inválido. Envie um arquivo .xlsx.",
        )

    # ------------------------------------------------------------------
    # 2. Salva arquivo temporário em disco
    # ------------------------------------------------------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        shutil.copyfileobj(arquivo.file, tmp)
        caminho_tmp = tmp.name

    # ------------------------------------------------------------------
    # 3. Executa o pipeline
    # ------------------------------------------------------------------
    try:
        resultado = processar_importacao(caminho_tmp, tabela)
    finally:
        # Remove o arquivo temporário independente do resultado
        if os.path.exists(caminho_tmp):
            os.remove(caminho_tmp)

    # ------------------------------------------------------------------
    # 4. Erro inesperado durante o pipeline
    # ------------------------------------------------------------------
    if resultado.mensagem_erro_inesperado:
        raise HTTPException(
            status_code=500,
            detail=(
                "Erro ao processar o arquivo. Verifique o formato ou tente novamente. "
                f"Log salvo em: {resultado.pasta_execucao}"
            ),
        )

    # ------------------------------------------------------------------
    # 5. Erros de validação → retorna JSON com erros (sem SQL)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # 6. Sucesso → retorna arquivo SQL para download
    #    Avisos (se houver) vão como header customizado
    # ------------------------------------------------------------------
    headers = {}
    if resultado.avisos:
        # Header com total de avisos — detalhes no avisos.txt da pasta
        headers["X-Avisos"] = str(len(resultado.avisos))
        headers["X-Avisos-Detalhes"] = f"Ver {resultado.pasta_execucao}/avisos.txt"

    return FileResponse(
        path=resultado.caminho_sql,
        media_type="text/plain",
        filename="inserts_pacientes.txt",
        headers=headers,
    )


# =============================================================================
# ENDPOINT DE SAÚDE
# =============================================================================

@app.get("/health")
def health():
    """Verifica se a API está no ar."""
    return {"status": "ok"}
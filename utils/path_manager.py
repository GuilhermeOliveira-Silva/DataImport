from datetime import datetime
from pathlib import Path


# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

PASTA_BASE = Path("output")


# =============================================================================
# FUNÇÕES
# =============================================================================

def gerar_nome_pasta() -> str:
    """
    Gera o nome da pasta baseado na data e hora atual.
    Formato: YYYY-MM-DD_HH-MM

    Returns:
        String com o nome da pasta. Ex: '2026-05-02_14-30'
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M")


def criar_pasta_execucao() -> Path:
    """
    Cria e retorna a pasta exclusiva desta execução dentro de output/.

    Se por algum motivo já existir uma pasta com o mesmo nome
    (duas execuções no mesmo minuto), adiciona sufixo _1, _2, etc.
    para nunca sobrescrever arquivos existentes.

    Returns:
        Path da pasta criada. Ex: Path('output/2026-05-02_14-30')
    """
    nome_base = gerar_nome_pasta()
    pasta = PASTA_BASE / nome_base

    # Evita colisão: output/2026-05-02_14-30_1, _2, etc.
    sufixo = 1
    while pasta.exists():
        pasta = PASTA_BASE / f"{nome_base}_{sufixo}"
        sufixo += 1

    pasta.mkdir(parents=True, exist_ok=False)
    print(f"      📁 Pasta de saída criada: {pasta}")
    return pasta


def caminho_arquivo(pasta: Path, nome_arquivo: str) -> str:
    """
    Monta o caminho completo de um arquivo dentro da pasta de execução.
    Retorna string para manter compatibilidade com open() e os.makedirs().

    Args:
        pasta:        Path retornado por criar_pasta_execucao()
        nome_arquivo: Nome do arquivo. Ex: 'inserts_pacientes.txt'

    Returns:
        Caminho completo como string. Ex: 'output/2026-05-02_14-30/inserts_pacientes.txt'
    """
    return str(pasta / nome_arquivo)
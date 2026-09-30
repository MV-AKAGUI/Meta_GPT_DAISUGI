"""
Módulo de Configuração de Caminhos: Google Drive & MetaGPT
Projeto: Sistema de Auditoria e Prestação de Contas Condominial (MetaGPT + Docling + LangChain)
Condomínio Only Guillmon
"""

from pathlib import Path
import os
import sys

# Diretório raiz da aplicação MetaGPT
APP_ROOT = Path(__file__).resolve().parent.parent

# Caminhos do repositório no Google Drive (com fallback para atalho ID ou override por ENV)
ENV_DRIVE_PATH = os.getenv("CONDO_AUDIT_DRIVE_PATH")

CANDIDATE_DRIVE_PATHS = [
    Path(r"G:\Meu Drive\Only_Guillmon_Prest_de_Contas"),
    Path(r"G:\.shortcut-targets-by-id\1lTNzVL3q-bBnhGq-RfnQCibuuGGyHXlX\Only_Guillmon_Prest_de_Contas"),
    Path(r"G:\Drives compartilhados\Only_Guillmon_Prest_de_Contas"),
]

if ENV_DRIVE_PATH:
    CANDIDATE_DRIVE_PATHS.insert(0, Path(ENV_DRIVE_PATH))


def get_drive_base_path() -> Path:
    """Retorna o caminho válido do Google Drive ou o padrão se nenhum for encontrado."""
    for path in CANDIDATE_DRIVE_PATHS:
        if path.exists() and path.is_dir():
            return path
    return CANDIDATE_DRIVE_PATHS[0]


DRIVE_BASE = get_drive_base_path()

# Camada de Ingestão "In Natura" (Landing Zone) e Revisão
IN_NATURA = DRIVE_BASE / "00_Documentos_In_Natura"
REVISAO_PENDENTE = DRIVE_BASE / "99_Revisao_Pendente"

# Pastas Canônicas Organizadas no Google Drive
ATAS_ASSEMBLEIAS = DRIVE_BASE / "01_Atas_e_Assembleias"
EXTRATOS_BANCARIOS = DRIVE_BASE / "02_Extratos_Bancarios"
NOTAS_FISCAIS_RECIBOS = DRIVE_BASE / "03_Notas_Fiscais_e_Recibos"
CONVENCAO_REGULAMENTO = DRIVE_BASE / "04_Convencao_e_Regulamento"
if not CONVENCAO_REGULAMENTO.exists() and (DRIVE_BASE / "04_Convenção_e_Regulamento").exists():
    CONVENCAO_REGULAMENTO = DRIVE_BASE / "04_Convenção_e_Regulamento"
PREVISAO_ORCAMENTARIA = DRIVE_BASE / "05_Previsao_Orcamentaria"

DRIVE_INPUT_DIRS = {
    "in_natura": IN_NATURA,
    "atas": ATAS_ASSEMBLEIAS,
    "extratos": EXTRATOS_BANCARIOS,
    "notas_fiscais": NOTAS_FISCAIS_RECIBOS,
    "convencao": CONVENCAO_REGULAMENTO,
    "previsao_orcamentaria": PREVISAO_ORCAMENTARIA,
    "revisao_pendente": REVISAO_PENDENTE,
}

# Pastas e Arquivos Locais da Aplicação
DATABASES_DIR = APP_ROOT / "databases"
CHROMA_DB_PATH = DATABASES_DIR / "chroma_db"
SQLITE_DB_PATH = DATABASES_DIR / "condo_audit.db"

OUTPUTS_DIR = APP_ROOT / "outputs"
OUTPUTS_RELATORIOS = OUTPUTS_DIR / "relatorios"
OUTPUTS_NOTIFICACOES = OUTPUTS_DIR / "notificacoes_juridicas"
OUTPUTS_TRIAGEM = OUTPUTS_DIR / "manifestos_triagem"


def ensure_local_directories():
    """Garante que todas as pastas locais da aplicação e do Drive existam."""
    local_dirs = [
        DATABASES_DIR,
        CHROMA_DB_PATH,
        OUTPUTS_RELATORIOS,
        OUTPUTS_NOTIFICACOES,
        OUTPUTS_TRIAGEM,
    ]
    for d in local_dirs:
        d.mkdir(parents=True, exist_ok=True)

    if DRIVE_BASE.exists():
        for d in DRIVE_INPUT_DIRS.values():
            d.mkdir(parents=True, exist_ok=True)


def verify_drive_integrity() -> dict:
    """
    Verifica a acessibilidade do Drive e contabiliza os documentos presentes.
    """
    ensure_local_directories()
    drive_accessible = DRIVE_BASE.exists() and DRIVE_BASE.is_dir()
    
    report = {
        "app_root": str(APP_ROOT),
        "drive_base": str(DRIVE_BASE),
        "drive_accessible": drive_accessible,
        "sqlite_db": str(SQLITE_DB_PATH),
        "chroma_db": str(CHROMA_DB_PATH),
        "categories": {}
    }

    for key, path in DRIVE_INPUT_DIRS.items():
        exists = path.exists() and path.is_dir()
        file_count = len([f for f in path.iterdir() if f.is_file()]) if exists else 0
        report["categories"][key] = {
            "path": str(path),
            "accessible": exists,
            "file_count": file_count
        }

    return report


if __name__ == "__main__":
    import json
    res = verify_drive_integrity()
    print("=== STATUS DE INTEGRIDADE DOS DIRETÓRIOS ===")
    print(f"App Root: {res['app_root']}")
    print(f"Drive Base: {res['drive_base']} (Acessível: {res['drive_accessible']})")
    print("\nPastas do Google Drive:")
    for k, v in res["categories"].items():
        status = "OK" if v["accessible"] else "FALHA"
        print(f"  - [{status}] {k}: {v['file_count']} arquivo(s) em {v['path']}")
    print("\nBancos Locais:")
    print(f"  - SQLite: {res['sqlite_db']}")
    print(f"  - ChromaDB: {res['chroma_db']}")

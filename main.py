"""
Ponto de Entrada Principal (CLI) - Sistema de Auditoria Condominial Only Guillmon
Arquitetura Holônica Multi-Agente com MetaGPT, Docling e LangChain
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Adiciona o diretório da aplicação ao sys.path
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from config.drive_paths import verify_drive_integrity
from tools.doc_triage import DocumentTriageEngine
from tools.drive_ingestor import DriveIngestor
from subagents.subagente_5_relator import SubagenteRelatorOrquestrador


def run_status():
    """Verifica e exibe a integridade do acoplamento Drive e Bancos."""
    res = verify_drive_integrity()
    print("\n" + "="*70)
    print("STATUS DO SISTEMA DE AUDITORIA CONDOMINIAL - ONLY GUILLMON")
    print("="*70)
    print(f"Aplicação Local: {res['app_root']}")
    print(f"Repositório Drive: {res['drive_base']} (Conectado: {res['drive_accessible']})")
    print("\nTaxonomia de Documentos no Google Drive:")
    for cat, info in res["categories"].items():
        status = "OK" if info["accessible"] else "FALHA"
        print(f"  [{status}] {cat:<22}: {info['file_count']:>3} arquivo(s) -> {info['path']}")
    print("\nBancos de Dados:")
    print(f"  • SQLite (Contábil): {res['sqlite_db']}")
    print(f"  • ChromaDB (Vetor):  {res['chroma_db']}")
    print("="*70 + "\n")


def run_triagem():
    """Executa o Subagente 0: Triagem e mineração da pasta In Natura."""
    print("\n" + "="*70)
    print("SUBAGENTE 0: MINERAÇÃO E TRIAGEM DOCUMENTAL (DOCLING + HEURÍSTICA)")
    print("="*70)
    engine = DocumentTriageEngine()
    engine.run_triage_batch()
    print("="*70 + "\n")


def run_ingestao():
    """Sincroniza as pastas canônicas do Drive para o SQLite e o ChromaDB."""
    print("\n" + "="*70)
    print("INGESTÃO E SINCRONIZAÇÃO: GOOGLE DRIVE -> SQLITE & CHROMADB")
    print("="*70)
    ingestor = DriveIngestor()
    ingestor.run_full_ingestion()
    print("="*70 + "\n")


async def run_auditoria():
    """Orquestra os 5 Subagentes especialistas via MetaGPT."""
    print("\n" + "="*70)
    print("PIPELINE MULTI-AGENTE: ORQUESTRAÇÃO GERAL DE AUDITORIA")
    print("="*70)
    relator = SubagenteRelatorOrquestrador()
    resultado = await relator.run("Executar ciclo integral de auditoria")
    print(resultado.content)
    print("="*70 + "\n")


async def run_pipeline_completo():
    """Executa toda a esteira do sistema de ponta a ponta."""
    run_status()
    run_triagem()
    run_ingestao()
    await run_auditoria()


def main():
    parser = argparse.ArgumentParser(
        description="Sistema Local de Auditoria e Conformidade Condominial com MetaGPT, Docling e LangChain"
    )
    parser.add_argument("--status", action="store_true", help="Exibe o status dos diretórios e bancos")
    parser.add_argument("--triagem", action="store_true", help="Executa o Subagente 0 para triar documentos da pasta In Natura")
    parser.add_argument("--ingestao", action="store_true", help="Sincroniza os arquivos do Drive para SQLite e ChromaDB")
    parser.add_argument("--auditar", action="store_true", help="Executa o pipeline multi-agente de auditoria (Subagentes 1 a 5)")
    parser.add_argument("--tudo", action="store_true", help="Executa o ciclo completo (Status + Triagem + Ingestão + Auditoria)")

    args = parser.parse_args()

    if args.status:
        run_status()
    elif args.triagem:
        run_triagem()
    elif args.ingestao:
        run_ingestao()
    elif args.auditar:
        asyncio.run(run_auditoria())
    elif args.tudo or len(sys.argv) == 1:
        asyncio.run(run_pipeline_completo())


if __name__ == "__main__":
    main()

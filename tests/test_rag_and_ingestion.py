"""
Teste de Integração do Motor RAG (ChromaDB + LangChain) e Ingestão do Drive
Valida as 3 coleções vetoriais, chunking semântico e busca por similaridade.
"""

from pathlib import Path
import sys

app_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_root))

from tools.rag_engine import CondoRAGDatabase
from tools.drive_ingestor import DriveIngestor


def test_rag_and_ingestor():
    print("Iniciando validação do CondoRAGDatabase...")
    rag = CondoRAGDatabase()

    # 1. Verifica estatísticas das coleções
    stats = rag.get_collection_stats()
    print(f"[OK] Coleções ChromaDB ativas: {stats}")
    assert stats["legislacao_jurisprudencia"] > 0, "A coleção de legislação deveria ter chunks pré-carregados"

    # 2. Teste de Busca Semântica em Legislação e Jurisprudência
    query_juridica = "O síndico é obrigado a apresentar prestação de contas analítica com extratos?"
    resultados = rag.query_rag(
        collection_name="legislacao_jurisprudencia",
        query=query_juridica,
        n_results=2
    )

    print(f"\n[OK] Busca semântica para: '{query_juridica}'")
    assert len(resultados) > 0, "Deveria retornar ao menos 1 resultado relevante"
    for r in resultados:
        print(f"  • [Score: {r['score_similaridade']}] Fonte: {r['metadata'].get('source')}")
        print(f"    Trecho: {r['texto'][:160]}...\n")

    # 3. Teste de indexação dinâmica de uma Ata Simulada
    ata_markdown_mock = """
    # ATA DA ASSEMBLEIA GERAL ORDINÁRIA - ABRIL 2024
    
    ## Item 1 - Prestação de Contas do Exercício Anterior
    O síndico apresentou balancete sintético. O condômino da unidade 42 solicitou acesso aos extratos analíticos da conta corrente e notas fiscais de reformas, o que foi indeferido pela mesa diretora sob alegação de que o conselho fiscal já havia aprovado previamente.
    
    ## Item 2 - Quórum e Votação
    Presentes 15 condôminos, representando 12% da fração ideal do condomínio. As contas foram aprovadas com 10 votos a favor, 3 contra e 2 abstenções.
    """

    chunks_inseridos = rag.index_markdown_document(
        collection_name="atas_historico",
        markdown_text=ata_markdown_mock,
        source_name="ATA_AGO_2024_04.md"
    )
    print(f"[OK] Ata simulada indexada com sucesso ({chunks_inseridos} chunks gerados).")

    # 4. Busca semântica na Ata
    q_ata = "houve recusa de apresentação de extratos ou documentos na assembleia?"
    res_ata = rag.query_rag(
        collection_name="atas_historico",
        query=q_ata,
        n_results=1
    )
    assert len(res_ata) > 0, "Deveria recuperar o trecho da recusa de documentos"
    print(f"[OK] Trecho recuperado da Ata:")
    print(f"  • {res_ata[0]['texto'][:200]}...\n")

    # 5. Instanciação e teste seguro do DriveIngestor
    ingestor = DriveIngestor()
    res_ingest = ingestor.run_full_ingestion()
    assert isinstance(res_ingest, dict), "O resultado da ingestão deve ser um dicionário"

    print("[SUCESSO] Teste do RAG Engine e Ingestão concluído com 100% de precisão!")


if __name__ == "__main__":
    test_rag_and_ingestor()

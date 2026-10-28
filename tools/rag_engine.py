"""
Motor de Memória Vetorial (ChromaDB + LangChain) para Auditoria e Compliance Condominial
Projeto: Sistema de Auditoria e Prestação de Contas Condominial (MetaGPT)
Condomínio Only Guillmon
Diretório de Persistência: databases/chroma_db/
"""

from pathlib import Path
import hashlib
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils import embedding_functions

from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.drive_paths import CHROMA_DB_PATH
from tools import laya_decisor


# Normas fundamentais pré-carregadas (Código Civil e Jurisprudência STJ sobre Prestação de Contas)
LEGISLACAO_STJ_BASE = """
# CÓDIGO CIVIL BRASILEIRO - CONDOMÍNIO EDILÍCIO

## Artigo 1.348 - Competências do Síndico
Compete ao síndico:
I - convocar a assembleia dos condôminos;
II - representar, ativa e passivamente, o condomínio, praticando, em juízo ou fora dele, os atos necessários à defesa dos interesses comuns;
III - dar imediato conhecimento à assembleia da existência de qualquer procedimento judicial ou administrativo, de interesse do condomínio;
IV - cumprir e fazer cumprir a convenção, o regimento interno e as determinações da assembleia;
V - diligenciar a conservação e a guarda das partes comuns e zelar pela prestação dos serviços que interessem aos possuidores;
VI - elaborar o orçamento da receita e da despesa relativa a cada ano;
VII - cobrar dos condôminos as suas contribuições, bem como impor e cobrar as multas devidas;
VIII - prestar contas à assembleia, anualmente e quando exigidas;
IX - realizar o seguro da edificação.

## Artigo 1.350 - Assembleia Geral Ordinária Anual
Convocará o síndico, anualmente, reunião da assembleia dos condôminos, na forma prevista na convenção, a fim de aprovar o orçamento das despesas, as contribuições dos condôminos e a prestação de contas, e eventualmente eleger-lhe o substituto e alterar o regimento interno.
§ 1º Se o síndico não convocar a assembleia, um quarto dos condôminos poderá fazê-lo.
§ 2º Se a assembleia não se reunir, o juiz decidirá, a requerimento de qualquer condômino.

## Artigo 1.352 e 1.353 - Quórum de Deliberações
Salvo quando exigido quórum especial neste Código ou na convenção condominial, as deliberações da assembleia serão tomadas, em primeira convocação, por maioria de votos dos condôminos presentes que representem pelo menos metade das frações ideais.
Em segunda convocação, a assembleia poderá deliberar por maioria dos votos dos presentes, salvo quando exigido quórum qualificado (ex: 2/3 para alteração de convenção ou obras voluptuárias).

# JURISPRUDÊNCIA DO SUPERIOR TRIBUNAL DE JUSTIÇA (STJ)

## Tese STJ: Dever de Prestação Analítica e Conciliação
A prestação de contas pelo síndico não pode ser meramente sintética ou por estimativa. O condômino tem direito legítimo à prestação de contas em forma contábil mercantil/analítica, instruída com os respectivos documentos justificativos (notas fiscais, recibos, folhas de pagamento e extratos bancários de todas as contas do condomínio).

## Tese STJ: Direito Individual do Condômino à Informação
O condômino possui interesse de agir e legitimidade para exigir a exibição integral de documentos contábeis e extratos bancários, independentemente de prévia deliberação assemblear, sempre que houver dúvida razoável, recusa de acesso ou indício de irregularidade na gestão financeira (Recurso Especial - REsp).

## Tese STJ: Responsabilidade Pessoal do Síndico e Gestão Temerária
A ausência de comprovação documental para saídas financeiras do condomínio ou apropriação indevida de valores enseja responsabilidade civil e criminal pessoal do síndico, com dever de ressarcimento integral ao caixa condominial por perdas e danos e enriquecimento sem causa (Art. 186 e 927 do Código Civil).
"""


class CondoRAGDatabase:
    """Gerenciador de RAG e Busca Semântica em ChromaDB."""

    COLLECTIONS = {
        "convencao_normas": "Convenção do Condomínio e Regimento Interno",
        "legislacao_jurisprudencia": "Código Civil, Lei 4.591/64 e Jurisprudência do STJ",
        "atas_historico": "Atas de AGOs e AGEs do Condomínio",
    }

    def __init__(self, persist_dir: Optional[Path] = None):
        self.persist_dir = persist_dir or CHROMA_DB_PATH
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        
        # Cliente persistente local
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        
        # Função de Embedding nativa (ONNX all-MiniLM-L6-v2 local, rápida e sem dependência de rede)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()
        
        self._init_collections()
        self._ensure_baseline_knowledge()

    def _init_collections(self):
        """Inicializa as 3 coleções canônicas de auditoria."""
        self.collections: Dict[str, Any] = {}
        for col_name in self.COLLECTIONS:
            self.collections[col_name] = self.client.get_or_create_collection(
                name=col_name,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )

    def _ensure_baseline_knowledge(self):
        """Assegura que a legislação base e acórdãos do STJ estejam sempre indexados."""
        col = self.collections["legislacao_jurisprudencia"]
        if col.count() == 0:
            print("[RAG] Indexando acervo base de Legislação e Jurisprudência do STJ...")
            self.index_markdown_document(
                collection_name="legislacao_jurisprudencia",
                markdown_text=LEGISLACAO_STJ_BASE,
                source_name="Codigo_Civil_STJ_Base.md"
            )

    def index_markdown_document(
        self,
        collection_name: str,
        markdown_text: str,
        source_name: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Divide o texto usando MarkdownHeaderTextSplitter e indexa no ChromaDB.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Coleção inválida: {collection_name}")

        col = self.collections[collection_name]

        # 1. Divisão por cabeçalhos de seções (H1, H2, H3)
        headers_to_split = [
            ("#", "secao_principal"),
            ("##", "subsecao"),
            ("###", "artigo_ou_clausula"),
        ]
        md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split,
            strip_headers=False
        )
        md_chunks = md_splitter.split_text(markdown_text)

        # 2. Divisão de chunks longos para manter precisão semântica
        char_splitter = RecursiveCharacterTextSplitter(
            chunk_size=900,
            chunk_overlap=120,
            separators=["\n\n", "\n", "Art.", "Cláusula", "§", ". "]
        )
        final_docs = char_splitter.split_documents(md_chunks)

        if not final_docs:
            return 0

        documents = []
        metadatas = []
        ids = []

        base_meta = {"source": source_name, **(extra_metadata or {})}

        for i, doc in enumerate(final_docs):
            doc_content = doc.page_content.strip()
            if not doc_content:
                continue

            chunk_id = hashlib.sha256(f"{source_name}_{i}_{doc_content[:60]}".encode()).hexdigest()[:16]
            
            # Combina metadados da hierarquia markdown
            chunk_meta = {**base_meta, **doc.metadata}
            
            documents.append(doc_content)
            metadatas.append(chunk_meta)
            ids.append(chunk_id)

        # Inserção / Upsert no ChromaDB
        col.upsert(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return len(documents)

    def query_rag(
        self,
        collection_name: str,
        query: str,
        n_results: int = 4,
        where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica por similaridade e retorna trechos contextuais.
        """
        if collection_name not in self.collections:
            raise ValueError(f"Coleção inválida: {collection_name}")

        col = self.collections[collection_name]
        kwargs = {
            "query_texts": [query],
            "n_results": n_results
        }
        if where_filter:
            kwargs["where"] = where_filter

        results = col.query(**kwargs)

        extracted = []
        if results and results.get("documents") and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
            dists = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metas, dists):
                extracted.append({
                    "texto": doc,
                    "metadata": meta,
                    "score_similaridade": round(1.0 - dist, 4) if dist is not None else 1.0
                })

        # Laya em sombra: julga se cada trecho responde à consulta, sem filtrar nada ainda.
        # Ao promover (evals/promover.py), o veredito passa a poder descartar trechos irrelevantes.
        for item in extracted:
            laya_decisor.sombra_sim_ou_nao(
                "metagpt.rag", f"Consulta: {query}\n\nTrecho: {item['texto'][:1500]}",
                "Este trecho contém informação que responde à consulta?", item["score_similaridade"])

        return extracted

    def get_collection_stats(self) -> Dict[str, int]:
        """Retorna a contagem de registros de cada coleção."""
        return {name: col.count() for name, col in self.collections.items()}


if __name__ == "__main__":
    rag = CondoRAGDatabase()
    stats = rag.get_collection_stats()
    print("=== STATUS DAS COLEÇÕES CHROMA DB ===")
    for k, v in stats.items():
        print(f"  • {k}: {v} documento(s) indexado(s)")

    # Teste de consulta
    test_q = "síndico é obrigado a apresentar extratos bancários?"
    res = rag.query_rag("legislacao_jurisprudencia", test_q, n_results=2)
    print(f"\nConsulta Teste: '{test_q}'")
    for r in res:
        print(f"  [Score: {r['score_similaridade']}] Fonte: {r['metadata'].get('source')}")
        print(f"  Trecho: {r['texto'][:180]}...\n")

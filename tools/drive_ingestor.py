"""
Módulo de Ingestão de Documentos do Google Drive para SQLite e ChromaDB
Projeto: Sistema de Auditoria e Prestação de Contas Condominial (MetaGPT)
Condomínio Only Guillmon
"""

from pathlib import Path
import re
import os
import csv
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.drive_paths import (
    ATAS_ASSEMBLEIAS,
    EXTRATOS_BANCARIOS,
    NOTAS_FISCAIS_RECIBOS,
    CONVENCAO_REGULAMENTO,
    PREVISAO_ORCAMENTARIA,
    SQLITE_DB_PATH,
    CHROMA_DB_PATH
)
from tools.sql_tool import CondoAuditDatabase
from tools.rag_engine import CondoRAGDatabase
from tools.doc_triage import compute_file_hash, DocumentTriageEngine


class DriveIngestor:
    """Ingere e sincroniza arquivos das pastas do Drive para as memórias relacional e vetorial."""

    def __init__(self):
        self.sql_db = CondoAuditDatabase()
        self.rag_db = CondoRAGDatabase()
        self.triage_engine = DocumentTriageEngine()

    def _extract_text_content(self, file_path: Path) -> str:
        """Extrai o texto rico (Markdown) via Docling/fallback."""
        return self.triage_engine.extract_content(file_path)

    # ================= 1. INGESTÃO DE ATAS (VETORIAL) =================

    def ingest_atas(self) -> int:
        """Processa as atas de assembleia e indexa no ChromaDB ('atas_historico')."""
        count = 0
        if not ATAS_ASSEMBLEIAS.exists():
            return 0

        for file_path in ATAS_ASSEMBLEIAS.iterdir():
            if file_path.is_file():
                text = self._extract_text_content(file_path)
                if text.strip():
                    n_chunks = self.rag_db.index_markdown_document(
                        collection_name="atas_historico",
                        markdown_text=text,
                        source_name=file_path.name,
                        extra_metadata={"tipo": "ata_assembleia", "arquivo": file_path.name}
                    )
                    count += 1
                    print(f"  [Atas] {file_path.name} indexada ({n_chunks} chunks).")
        return count

    # ================= 2. INGESTÃO DE CONVENÇÃO E REGULAMENTO (VETORIAL) =================

    def ingest_convencao(self) -> int:
        """Processa a convenção e regimento interno e indexa no ChromaDB ('convencao_normas')."""
        count = 0
        if not CONVENCAO_REGULAMENTO.exists():
            return 0

        for file_path in CONVENCAO_REGULAMENTO.iterdir():
            if file_path.is_file():
                text = self._extract_text_content(file_path)
                if text.strip():
                    n_chunks = self.rag_db.index_markdown_document(
                        collection_name="convencao_normas",
                        markdown_text=text,
                        source_name=file_path.name,
                        extra_metadata={"tipo": "norma_condominial", "arquivo": file_path.name}
                    )
                    count += 1
                    print(f"  [Convenção] {file_path.name} indexada ({n_chunks} chunks).")
        return count

    # ================= 3. INGESTÃO DE EXTRATOS BANCÁRIOS (RELACIONAL SQLITE) =================

    def ingest_extratos(self) -> int:
        """Processa extratos (CSV, OFX ou tabelas em PDF) e grava em extratos_bancarios."""
        count = 0
        if not EXTRATOS_BANCARIOS.exists():
            return 0

        for file_path in EXTRATOS_BANCARIOS.iterdir():
            if not file_path.is_file():
                continue

            suffix = file_path.suffix.lower()

            # Caso 1: Extrato em CSV
            if suffix == ".csv":
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Tenta mapear colunas usuais de extratos bancários
                            data_str = row.get("data") or row.get("Data") or datetime.now().strftime("%Y-%m-%d")
                            hist = row.get("historico") or row.get("Historico") or row.get("descricao") or "Lançamento"
                            val_str = str(row.get("valor") or row.get("Valor") or "0.0").replace(",", ".").replace("R$", "").strip()
                            try:
                                valor = float(val_str)
                            except ValueError:
                                valor = 0.0

                            tipo_op = "DEBITO" if valor < 0 else "CREDITO"
                            self.sql_db.insert_extrato_item({
                                "data": data_str,
                                "banco": "Banco Sincronizado",
                                "historico": hist,
                                "valor": valor,
                                "tipo_operacao": tipo_op,
                                "arquivo_origem": file_path.name
                            })
                            count += 1
                except Exception as e:
                    print(f"[Erro Extrato CSV] {file_path.name}: {e}")

            # Caso 2: Extrato em PDF / Texto minerado via Docling
            else:
                text = self._extract_text_content(file_path)
                lines = text.splitlines()
                for line in lines:
                    # Detecta padrões de linhas contábeis: DD/MM/AAAA ou DD/MM + Descrição + Valor
                    match = re.search(r"(\d{2}[/-]\d{2}(?:[/-]\d{2,4})?)\s+(.+?)\s+(-?R?\$?\s*[\d\.,]+)", line)
                    if match:
                        data_raw, hist, val_raw = match.groups()
                        val_clean = val_raw.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        try:
                            valor = float(val_clean)
                            if "deb" in hist.lower() or "pagto" in hist.lower() or "pix enviado" in hist.lower() or "tar" in hist.lower():
                                if valor > 0:
                                    valor = -valor
                            tipo_op = "DEBITO" if valor < 0 else "CREDITO"
                            self.sql_db.insert_extrato_item({
                                "data": data_raw,
                                "banco": "Extrato Documental",
                                "historico": hist.strip(),
                                "valor": valor,
                                "tipo_operacao": tipo_op,
                                "arquivo_origem": file_path.name
                            })
                            count += 1
                        except ValueError:
                            continue
        return count

    # ================= 4. INGESTÃO DE NOTAS FISCAIS E RECIBOS (RELACIONAL SQLITE) =================

    def ingest_notas_fiscais(self) -> int:
        """Extrai metadados de notas fiscais e alimenta a tabela lancamentos_financeiros."""
        count = 0
        if not NOTAS_FISCAIS_RECIBOS.exists():
            return 0

        for file_path in NOTAS_FISCAIS_RECIBOS.iterdir():
            if not file_path.is_file():
                continue

            text = self._extract_text_content(file_path)
            # Regex para valor total de NF
            val_match = re.search(r"(?:valor\s+total|total\s+da\s+nota|valor\s+do\s+serviço|total)\s*[:=]?\s*R?\$?\s*([\d\.,]+)", text, re.IGNORECASE)
            valor = 0.0
            if val_match:
                try:
                    valor = float(val_match.group(1).replace(".", "").replace(",", ".").strip())
                except ValueError:
                    valor = 0.0

            # Regex para CNPJ
            cnpj_match = re.search(r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b", text)
            cnpj = cnpj_match.group(0) if cnpj_match else None

            # Regex para data
            date_match = re.search(r"\b(\d{2}[/-]\d{2}[/-]\d{4})\b", text)
            data_nf = date_match.group(1) if date_match else datetime.now().strftime("%Y-%m-%d")

            # Identificação do número do documento
            doc_num_match = re.search(r"(?:número|nº|nf-e|danfe|nota\s+fiscal)\s*[:=]?\s*(\d+)", text, re.IGNORECASE)
            doc_num = doc_num_match.group(1) if doc_num_match else file_path.stem

            self.sql_db.insert_lancamento({
                "data": data_nf,
                "categoria": "Despesa Condominial",
                "descricao": f"Comprovante referente a {file_path.stem}",
                "valor": valor,
                "tipo_operacao": "DEBITO",
                "numero_documento": doc_num,
                "favorecido": "Fornecedor Identificado em NF",
                "cnpj_cpf": cnpj,
                "status_conciliacao": "PENDENTE_COMPROVANTE",
                "arquivo_origem": file_path.name
            })
            count += 1
            print(f"  [NF/Recibo] {file_path.name} -> R$ {valor:.2f} (CNPJ: {cnpj or 'Não detectado'})")
        return count

    # ================= 5. INGESTÃO DE PREVISÃO ORÇAMENTÁRIA (SQLITE) =================

    def ingest_previsao_orcamentaria(self) -> int:
        """Lê balancetes orçamentários e registra tetos anuais na tabela previsao_orcamentaria."""
        count = 0
        if not PREVISAO_ORCAMENTARIA.exists():
            return 0

        for file_path in PREVISAO_ORCAMENTARIA.iterdir():
            if not file_path.is_file():
                continue

            text = self._extract_text_content(file_path)
            lines = text.splitlines()
            ano_atual = datetime.now().year

            for line in lines:
                # Procura por linhas no formato: Categoria + Valor Mensal + Valor Anual
                match = re.search(r"([A-Za-zÀ-ÖØ-öø-ÿ\s]{4,}?)\s+R?\$?\s*([\d\.,]+)\s+R?\$?\s*([\d\.,]+)", line)
                if match:
                    cat, val_m_raw, val_a_raw = match.groups()
                    try:
                        val_m = float(val_m_raw.replace(".", "").replace(",", ".").strip())
                        val_a = float(val_a_raw.replace(".", "").replace(",", ".").strip())
                        self.sql_db.insert_previsao_item({
                            "ano_exercicio": ano_atual,
                            "categoria": cat.strip(),
                            "valor_aprovado_mensal": val_m,
                            "valor_aprovado_anual": val_a,
                            "ref_ata_ago": f"Previsão {ano_atual} - {file_path.stem}",
                            "arquivo_origem": file_path.name
                        })
                        count += 1
                    except ValueError:
                        continue
        return count

    def run_full_ingestion(self) -> Dict[str, Any]:
        """Executa a sincronização completa de todas as pastas do Google Drive."""
        print("=== INICIANDO SINCRONIZAÇÃO COMPLETA DO GOOGLE DRIVE ===")
        res = {
            "timestamp": datetime.now().isoformat(),
            "atas_indexadas": self.ingest_atas(),
            "convencoes_indexadas": self.ingest_convencao(),
            "extratos_gravados": self.ingest_extratos(),
            "notas_fiscais_gravadas": self.ingest_notas_fiscais(),
            "previsoes_gravadas": self.ingest_previsao_orcamentaria(),
            "chroma_stats": self.rag_db.get_collection_stats()
        }
        print("\n=== RESUMO DA INGESTÃO ===")
        print(f"  • Atas no RAG: {res['atas_indexadas']}")
        print(f"  • Normas/Convenção no RAG: {res['convencoes_indexadas']}")
        print(f"  • Linhas de Extrato no SQLite: {res['extratos_gravados']}")
        print(f"  • Notas Fiscais no SQLite: {res['notas_fiscais_gravadas']}")
        print(f"  • Itens de Orçamento no SQLite: {res['previsoes_gravadas']}")
        print(f"  • Estatísticas do ChromaDB: {res['chroma_stats']}")
        return res


if __name__ == "__main__":
    ingestor = DriveIngestor()
    ingestor.run_full_ingestion()

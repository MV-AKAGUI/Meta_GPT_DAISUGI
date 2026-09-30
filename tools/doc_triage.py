"""
Módulo de Triagem e Mineração Documental (Subagente 0)
Utiliza Docling + Heurística e Regras Semânticas para ingerir da pasta '00_Documentos_In_Natura'
e distribuir com rastreabilidade para as pastas canônicas do Google Drive.
"""

from pathlib import Path
import os
import re
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

# Importação dos caminhos centrais
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.drive_paths import (
    IN_NATURA,
    REVISAO_PENDENTE,
    ATAS_ASSEMBLEIAS,
    EXTRATOS_BANCARIOS,
    NOTAS_FISCAIS_RECIBOS,
    CONVENCAO_REGULAMENTO,
    PREVISAO_ORCAMENTARIA,
    OUTPUTS_TRIAGEM,
    verify_drive_integrity,
)


def compute_file_hash(file_path: Path) -> str:
    """Calcula o hash SHA256 do arquivo para rastreabilidade e evitar duplicidade."""
    sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


class DocumentClassifier:
    """
    Classificador especializado para documentos condominiais.
    Utiliza pontuação ponderada por relevância de termos-chave e expressões regulares.
    """

    CATEGORIES = {
        "atas": {
            "target_dir": ATAS_ASSEMBLEIAS,
            "patterns": [
                r"\bassembleia\s+geral\s+ordin[aá]ria\b",
                r"\bassembleia\s+geral\s+extraordin[aá]ria\b",
                r"\bedital\s+de\s+convoca[cç][aã]o\b",
                r"\bata\s+da\s+(\d+ª|[a-z]+)\s+assembleia\b",
                r"\belei[cç][aã]o\s+de\s+s[ií]ndico\b",
                r"\bconselho\s+fiscal\b",
                r"\bqu[oó]rum\s+de\s+aprova[cç][aã]o\b",
                r"\blista\s+de\s+presen[cç]a\b",
            ],
            "keywords": ["assembleia", "ata", "deliberação", "convocação", "síndico", "conselheiros"],
            "weight": 1.2
        },
        "extratos": {
            "target_dir": EXTRATOS_BANCARIOS,
            "patterns": [
                r"\bextrato\s+(mensal|de\s+conta|banc[aá]rio)\b",
                r"\bsaldo\s+(anterior|atual|dispon[ií]vel|bloqueado)\b",
                r"\blan[cç]amentos\s+do\s+per[ií]odo\b",
                r"\bbanco\s+(itau|itaú|bradesco|santander|brasil|caixa|inter|nubank)\b",
                r"\baplica[cç][aã]o\s+financeira\b",
                r"\bresgate\s+autom[aá]tico\b",
            ],
            "keywords": ["extrato", "agência", "conta corrente", "tarifa bancária", "pix recebido", "ted enviada"],
            "weight": 1.3
        },
        "notas_fiscais": {
            "target_dir": NOTAS_FISCAIS_RECIBOS,
            "patterns": [
                r"\bdanfe\b",
                r"\bdocumento\s+auxiliar\s+da\s+nota\s+fiscal\b",
                r"\bnota\s+fiscal\s+de\s+servi[cç]os?\b",
                r"\bnfs-?e\b",
                r"\bcomprovante\s+de\s+pagamento\b",
                r"\brecibo\s+de\s+pagamento\b",
                r"\bchave\s+de\s+acesso\b",
                r"\bautentica[cç][aã]o\s+banc[aá]ria\b",
                r"\bcnpj\s+do\s+prestador\b",
            ],
            "keywords": ["danfe", "nfe", "nfse", "recibo", "nota fiscal", "inscrição municipal", "retencao iss"],
            "weight": 1.1
        },
        "convencao": {
            "target_dir": CONVENCAO_REGULAMENTO,
            "patterns": [
                r"\bconven[cç][aã]o\s+(do\s+)?condom[ií]nio\b",
                r"\bregimento\s+interno\b",
                r"\bregulamento\s+interno\b",
                r"\bfra[cç][aã]o\s+ideal\b",
                r"\bdireitos\s+e\s+deveres\s+dos\s+cond[oô]minos\b",
                r"\bdestina[cç][aã]o\s+das\s+unidades\b",
            ],
            "keywords": ["convenção", "regimento interno", "cláusula", "frações ideais", "administração do condomínio"],
            "weight": 1.4
        },
        "previsao_orcamentaria": {
            "target_dir": PREVISAO_ORCAMENTARIA,
            "patterns": [
                r"\bprevis[aã]o\s+or[cç]ament[aá]ria\b",
                r"\bor[cç]ado\s+(x|vs\.?)\s+realizado\b",
                r"\bbalancete\s+(sint[eé]tico|financeiro|anual)\b",
                r"\bplano\s+or[cç]ament[aá]rio\b",
                r"\bdespesas\s+ordin[aá]rias\s+previstas\b",
                r"\bfundo\s+de\s+reserva\s+previsto\b",
            ],
            "keywords": ["previsão orçamentária", "orçado", "balancete sintético", "cota condominial estimada"],
            "weight": 1.2
        },
    }

    @classmethod
    def classify_text(cls, text: str, filename: str = "") -> Dict[str, Any]:
        """
        Avalia o texto e nome do arquivo, calculando o score de cada categoria.
        """
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        scores: Dict[str, float] = {}
        matched_details: Dict[str, List[str]] = {}

        for cat_name, cat_data in cls.CATEGORIES.items():
            score = 0.0
            matches = []

            # 1. Checagem no nome do arquivo (forte sinal)
            for kw in cat_data["keywords"]:
                if kw in filename_lower:
                    score += 3.0
                    matches.append(f"filename_keyword:{kw}")

            # 2. Expressões regulares no conteúdo
            for pattern in cat_data["patterns"]:
                found = re.findall(pattern, text_lower)
                if found:
                    score += len(found) * 2.0
                    matches.append(f"pattern:{pattern}")

            # 3. Palavras-chave no corpo
            for kw in cat_data["keywords"]:
                count = text_lower.count(kw)
                if count > 0:
                    score += min(count, 5) * 0.5
                    matches.append(f"keyword:{kw}({count})")

            # Aplica o peso da categoria
            scores[cat_name] = round(score * cat_data["weight"], 2)
            matched_details[cat_name] = matches

        # Determina o vencedor
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]

        # Limiar de confiança (mínimo de pontuação para não cair em revisão pendente)
        confidence = min(round(best_score / 15.0, 2), 1.0) if best_score > 0 else 0.0

        if best_score < 4.0:
            category_result = "revisao_pendente"
            target_dir = REVISAO_PENDENTE
        else:
            category_result = best_category
            target_dir = cls.CATEGORIES[best_category]["target_dir"]

        return {
            "categoria": category_result,
            "target_dir": target_dir,
            "score": best_score,
            "confianca": confidence,
            "scores_completos": scores,
            "evidencias": matched_details.get(best_category, [])
        }


class DocumentTriageEngine:
    """
    Motor que orquestra a leitura via Docling (com fallback) e despacho dos arquivos.
    """

    def __init__(self):
        verify_drive_integrity()
        self._docling_converter = None

    def _get_docling_converter(self):
        """Inicialização tardia (lazy load) do DocumentConverter do Docling."""
        if self._docling_converter is None:
            try:
                from docling.document_converter import DocumentConverter
                self._docling_converter = DocumentConverter()
            except Exception as e:
                print(f"[Aviso] Não foi possível carregar DocumentConverter: {e}")
                self._docling_converter = None
        return self._docling_converter

    def extract_content(self, file_path: Path) -> str:
        """
        Extrai o texto do arquivo usando Docling se for PDF/documento complexo,
        ou leitura nativa para texto/OFX/CSV.
        """
        suffix = file_path.suffix.lower()

        # Arquivos de texto puro / OFX / CSV
        if suffix in [".txt", ".csv", ".ofx", ".json", ".log"]:
            try:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                return file_path.read_text(encoding="latin1", errors="ignore")

        # Arquivos PDF / DOCX via Docling
        if suffix in [".pdf", ".docx", ".pptx", ".html"]:
            converter = self._get_docling_converter()
            if converter:
                try:
                    res = converter.convert(str(file_path))
                    # Retorna o documento em Markdown (com tabelas preservadas)
                    return res.document.export_to_markdown()
                except Exception as e:
                    print(f"[Docling Fallback] Falha ao converter {file_path.name}: {e}")

            # Fallback rápido para PDF se o Docling falhar ou estiver ocupado
            if suffix == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(str(file_path))
                    pages_text = [p.extract_text() or "" for p in reader.pages[:10]]
                    return "\n".join(pages_text)
                except Exception:
                    pass

        return ""

    def extract_reference_date(self, text: str, filename: str) -> Optional[str]:
        """Tenta detectar o ano/mês de competência (Ex: 2024-05)."""
        combined = f"{filename} {text[:2000]}"
        # Busca padrões YYYY-MM ou MM/YYYY ou MM-YYYY
        m1 = re.search(r"\b(202[0-9])[-_/.](0[1-9]|1[0-2])\b", combined)
        if m1:
            return f"{m1.group(1)}-{m1.group(2)}"
        m2 = re.search(r"\b(0[1-9]|1[0-2])[-_/.](202[0-9])\b", combined)
        if m2:
            return f"{m2.group(2)}-{m2.group(1)}"
        return None

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Mina, classifica, renomeia e move um arquivo de 00_In_Natura para o destino correto.
        """
        original_name = file_path.name
        file_hash = compute_file_hash(file_path)

        # 1. Extração do conteúdo
        text = self.extract_content(file_path)

        # 2. Classificação
        classification = DocumentClassifier.classify_text(text, filename=original_name)
        target_dir: Path = classification["target_dir"]

        # 3. Competência temporal
        ref_date = self.extract_reference_date(text, original_name)
        date_prefix = ref_date if ref_date else datetime.now().strftime("%Y-%m")

        # 4. Normalização do nome final
        clean_basename = re.sub(r"[^\w\-\.]", "_", original_name)
        target_filename = f"{date_prefix}_{classification['categoria']}_{clean_basename}"
        target_path = target_dir / target_filename

        # Evita sobrescrita se já existir com mesmo nome
        if target_path.exists():
            target_filename = f"{date_prefix}_{classification['categoria']}_{file_hash[:8]}_{clean_basename}"
            target_path = target_dir / target_filename

        # 5. Movimentação segura do arquivo
        shutil.move(str(file_path), str(target_path))

        record = {
            "timestamp": datetime.now().isoformat(),
            "nome_original": original_name,
            "nome_destino": target_filename,
            "caminho_origem": str(file_path),
            "caminho_destino": str(target_path),
            "categoria": classification["categoria"],
            "confianca": classification["confianca"],
            "score": classification["score"],
            "sha256": file_hash,
            "tamanho_bytes": target_path.stat().st_size,
            "evidencias": classification["evidencias"],
        }

        return record

    def run_triage_batch(self) -> Dict[str, Any]:
        """
        Varre a pasta 00_Documentos_In_Natura e processa todos os arquivos pendentes.
        """
        pending_files = [f for f in IN_NATURA.iterdir() if f.is_file()]
        
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        manifest = {
            "batch_id": batch_id,
            "total_arquivos": len(pending_files),
            "data_execucao": datetime.now().isoformat(),
            "processados": [],
            "erros": []
        }

        if not pending_files:
            print("Nenhum arquivo encontrado em '00_Documentos_In_Natura'.")
            return manifest

        print(f"Iniciando triagem de {len(pending_files)} arquivo(s) in natura...")

        for f in pending_files:
            try:
                rec = self.process_file(f)
                manifest["processados"].append(rec)
                print(f"  -> [{rec['categoria'].upper()}] {rec['nome_original']} => {rec['nome_destino']} (Confiança: {rec['confianca']*100:.0f}%)")
            except Exception as e:
                err_info = {"arquivo": f.name, "erro": str(e)}
                manifest["erros"].append(err_info)
                print(f"  -> [ERRO] {f.name}: {e}")

        # Salva o manifesto de triagem para auditoria e rastreabilidade total
        OUTPUTS_TRIAGEM.mkdir(parents=True, exist_ok=True)
        manifest_file = OUTPUTS_TRIAGEM / f"manifesto_triagem_{batch_id}.json"
        with open(manifest_file, "w", encoding="utf-8") as m_out:
            json.dump(manifest, m_out, indent=2, ensure_ascii=False)

        print(f"\nManifesto de triagem salvo em: {manifest_file}")
        return manifest


if __name__ == "__main__":
    engine = DocumentTriageEngine()
    engine.run_triage_batch()

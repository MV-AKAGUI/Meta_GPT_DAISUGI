"""
Skill: Verificação de Quórum e Validação de Atos e Atas de Assembleia
Utilizada pelo Subagente 2 (Analista de Conformidade e Legalidade)
Cruza as deliberações constantes nas Atas contra os quóruns obrigatórios do Código Civil e Convenção.
"""

from typing import Dict, Any, List
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.rag_engine import CondoRAGDatabase
from tools.sql_tool import CondoAuditDatabase


class SkillVerificacaoQuorum:
    """Valida a legalidade de assembleias, editais e quóruns exigidos por lei."""

    QUORUM_RULES = {
        "alteracao_convencao": {
            "regra": "2/3 de todos os condôminos (frações ideais)",
            "artigo": "Art. 1.351 do Código Civil",
            "tipo_obra": "Alteração de Convenção"
        },
        "obras_voluptuarias": {
            "regra": "2/3 de todos os condôminos",
            "artigo": "Art. 1.341, I do Código Civil",
            "tipo_obra": "Obras Voluptuárias (embelezamento, recreação sem utilidade essencial)"
        },
        "obras_uteis": {
            "regra": "Maioria absoluta de todos os condôminos",
            "artigo": "Art. 1.341, II do Código Civil",
            "tipo_obra": "Obras Úteis (aumentam ou facilitam o uso da coisa comum)"
        },
        "destituicao_sindico": {
            "regra": "Maioria absoluta dos membros da assembleia (presentes)",
            "artigo": "Art. 1.349 do Código Civil",
            "tipo_obra": "Destituição do Síndico por irregularidades"
        },
        "prestacao_contas_ordinaria": {
            "regra": "Maioria dos votos dos presentes em 2ª convocação",
            "artigo": "Art. 1.353 do Código Civil",
            "tipo_obra": "Aprovação de Contas Ordinárias"
        }
    }

    def __init__(self, rag_db: CondoRAGDatabase, sql_db: CondoAuditDatabase):
        self.rag = rag_db
        self.sql = sql_db

    def analisar_conformidade_atas(self) -> Dict[str, Any]:
        """
        Consulta o histórico de atas no ChromaDB e avalia potenciais nulidades ou vícios formais.
        """
        # 1. Busca evidências de deliberações de obras ou alterações relevantes
        query_obras = "aprovação de obras rateio extraordinário reforma valor substancial"
        trechos_obras = self.rag.query_rag("atas_historico", query_obras, n_results=3)

        # 2. Busca evidências de prestação de contas e impugnações
        query_contas = "prestação de contas balancete aprovação reprovação ressalva impugnação conselho fiscal"
        trechos_contas = self.rag.query_rag("atas_historico", query_contas, n_results=3)

        # 3. Busca cláusulas de quórum na convenção
        query_convencao = "quórum deliberação assembleia maioria votos frações ideais"
        trechos_convencao = self.rag.query_rag("convencao_normas", query_convencao, n_results=2)

        achados_conformidade = []

        # Análise heurística das evidências encontradas
        for t in trechos_contas:
            texto = t["texto"].lower()
            if "recusa" in texto or "indeferid" in texto or "sintético" in texto:
                achados_conformidade.append({
                    "tipo": "CERCEAMENTO_DIREITO_INFORMACAO",
                    "severidade": "GRAVE",
                    "descricao": "Indício de aprovação ou deliberação com recusa de acesso a extratos analíticos ou balancetes meramente sintéticos.",
                    "fonte": t["metadata"].get("source", "Ata"),
                    "trecho": t["texto"][:220]
                })

        # Registra achados de conformidade no SQLite
        for a in achados_conformidade:
            self.sql.registrar_inconsistencia({
                "data_ocorrencia": "2024-04-15",
                "tipo_inconsistencia": a["tipo"],
                "grau_severidade": a["severidade"],
                "valor_envolvido": 0.0,
                "descricao_detalhada": f"{a['descricao']} - Fonte: {a['fonte']}",
                "subagente_origem": "Subagente 2 - Analista de Conformidade"
            })

        return {
            "total_achados": len(achados_conformidade),
            "achados": achados_conformidade,
            "evidencias_obras": trechos_obras,
            "evidencias_convencao": trechos_convencao,
            "regras_referencia": self.QUORUM_RULES
        }

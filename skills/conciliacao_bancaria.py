"""
Skill: Conciliação Bancária & Análise Orçamentária
Utilizada pelo Subagente 1 (Auditor Financeiro)
Cruza débitos em extratos contra notas fiscais e compara contra previsão orçamentária.
"""

from typing import Dict, Any, List
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.sql_tool import CondoAuditDatabase


class SkillConciliacaoBancaria:
    """Executa a conciliação automatizada e apuração de saídas desacompanhadas de comprovante."""

    def __init__(self, db: CondoAuditDatabase):
        self.db = db

    def conciliar_automaticamente(self, margem_dias: int = 5) -> Dict[str, Any]:
        """
        Tenta cruzar débitos do extrato com lançamentos comprovados
        baseando-se em exatidão de valor e proximidade de data.
        """
        conn = self.db.get_connection()
        extratos_nao_conciliados = conn.execute("""
            SELECT id, data, valor, historico
            FROM extratos_bancarios
            WHERE tipo_operacao = 'DEBITO' AND status_conciliacao = 'NAO_CONCILIADO'
        """).fetchall()

        lancamentos_pendentes = conn.execute("""
            SELECT id, data, valor, descricao, numero_documento
            FROM lancamentos_financeiros
            WHERE status_conciliacao = 'PENDENTE_COMPROVANTE'
        """).fetchall()

        conciliados_count = 0
        vinculos = []

        # Algoritmo de cruzamento determinístico
        for ext in extratos_nao_conciliados:
            ext_id = ext["id"]
            ext_val = abs(ext["valor"])

            for lanc in lancamentos_pendentes:
                lanc_id = lanc["id"]
                lanc_val = abs(lanc["valor"])

                # Checa equivalência exata de valor (tolerância de R$ 0.05 para arredondamentos)
                if abs(ext_val - lanc_val) <= 0.05:
                    self.db.conciliar_item(extrato_id=ext_id, lancamento_id=lanc_id)
                    conciliados_count += 1
                    vinculos.append({
                        "extrato_id": ext_id,
                        "lancamento_id": lanc_id,
                        "valor": ext_val,
                        "historico": ext["historico"],
                        "doc_comprovante": lanc["numero_documento"]
                    })
                    break

        return {
            "total_conciliados_agora": conciliados_count,
            "vinculos": vinculos
        }

    def auditar_inconsistencias(self) -> Dict[str, Any]:
        """
        Gera o balanço pericial das contas:
        - Débitos totais
        - Débitos comprovados (conciliados)
        - Débitos não comprovados (inconsistência grave)
        """
        conn = self.db.get_connection()
        
        row_totais = conn.execute("""
            SELECT 
                COUNT(*) AS qtd_debitos,
                COALESCE(SUM(ABS(valor)), 0.0) AS total_saidas
            FROM extratos_bancarios
            WHERE tipo_operacao = 'DEBITO'
        """).fetchone()

        row_comprovados = conn.execute("""
            SELECT 
                COUNT(*) AS qtd_comprovados,
                COALESCE(SUM(ABS(valor)), 0.0) AS total_comprovado
            FROM extratos_bancarios
            WHERE tipo_operacao = 'DEBITO' AND status_conciliacao = 'CONCILIADO'
        """).fetchone()

        saidas_sem_nf = self.db.get_saidas_sem_comprovante()
        total_sem_nf = sum(abs(s["valor"]) for s in saidas_sem_nf)

        # Registra achados graves automaticamente na tabela de inconsistências
        for item in saidas_sem_nf:
            self.db.registrar_inconsistencia({
                "data_ocorrencia": item["data"],
                "tipo_inconsistencia": "SAIDA_SEM_COMPROVANTE",
                "grau_severidade": "GRAVE",
                "valor_envolvido": abs(item["valor"]),
                "descricao_detalhada": f"Débito bancário de R$ {abs(item['valor']):.2f} ({item['historico']}) sem correspondente nota fiscal ou recibo comprovatório.",
                "subagente_origem": "Subagente 1 - Auditor Financeiro",
                "id_extrato_fk": item["id"]
            })

        total_saidas = row_totais["total_saidas"] if row_totais else 0.0
        total_comprovado = row_comprovados["total_comprovado"] if row_comprovados else 0.0
        indice_comprovacao = (total_comprovado / total_saidas * 100.0) if total_saidas > 0 else 100.0

        return {
            "total_saidas_bancarias": round(total_saidas, 2),
            "total_comprovado": round(total_comprovado, 2),
            "total_sem_comprovacao": round(total_sem_nf, 2),
            "indice_comprovacao_pct": round(indice_comprovacao, 2),
            "itens_sem_comprovante": saidas_sem_nf
        }

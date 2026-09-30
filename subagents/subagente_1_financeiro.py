"""
Subagente 1: Auditor Financeiro (MetaGPT Role)
Responsável por conciliação bancária exaustiva, identificação de saídas sem comprovante
e análise de desvios orçamentários.
"""

from pathlib import Path
import json
import asyncio
from typing import Dict, Any

from metagpt.roles import Role
from metagpt.actions import Action
from metagpt.schema import Message

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.sql_tool import CondoAuditDatabase
from skills.conciliacao_bancaria import SkillConciliacaoBancaria


SYSTEM_PROMPT_FINANCEIRO = """Você é o Subagente 1: Auditor Financeiro do condomínio 'Only Guillmon'.
Sua função é realizar a conciliação bancária exaustiva, cruzando cada débito no extrato bancário com a nota fiscal correspondente no banco SQLite.
Exija 100% de comprovação documental para cada saída de caixa.
Classifique qualquer saída sem nota fiscal/recibo formal como 'Inconsistência Financeira Grave' com dever de restituição ao caixa.
Apresente os números consolidados de forma pericial e incontestável.
"""


class AuditarFinancasAction(Action):
    """Ação que executa a conciliação e gera o relatório financeiro analítico."""

    name: str = "AuditarFinancasAction"

    async def run(self, instrucao: str = "") -> str:
        db = CondoAuditDatabase()
        skill = SkillConciliacaoBancaria(db)

        # 1. Conciliação automática
        res_conc = skill.conciliar_automaticamente()
        
        # 2. Levantamento pericial de saídas sem comprovante
        balanco = skill.auditar_inconsistencias()

        # 3. Formatação do parecer financeiro
        total_saidas = balanco["total_saidas_bancarias"]
        total_comp = balanco["total_comprovado"]
        total_sem = balanco["total_sem_comprovacao"]
        indice = balanco["indice_comprovacao_pct"]
        qtd_orfas = len(balanco["itens_sem_comprovante"])

        relatorio = (
            f"=== PARECER DO AUDITOR FINANCEIRO (SUBAGENTE 1) ===\n"
            f"Período Auditado / Situação da Conciliação:\n"
            f"• Total de Débitos Bancários Identificados: R$ {total_saidas:,.2f}\n"
            f"• Total Comprovado por Notas Fiscais/Recibos: R$ {total_comp:,.2f}\n"
            f"• TOTAL NÃO COMPROVADO (INCONSISTÊNCIA GRAVE): R$ {total_sem:,.2f}\n"
            f"• Índice de Regularidade Documental: {indice:.1f}%\n"
            f"• Lançamentos Recém-Conciliados: {res_conc['total_conciliados_agora']}\n"
            f"• Quantidade de Saídas sem Comprovação: {qtd_orfas}\n\n"
        )

        if balanco["itens_sem_comprovante"]:
            relatorio += "DETALHAMENTO DAS SAÍDAS SEM COMPROVAÇÃO DOCUMENTAL (IRREGULARIDADE GRAVE):\n"
            for item in balanco["itens_sem_comprovante"]:
                relatorio += f"  - [{item['data']}] {item['historico']} | R$ {abs(item['valor']):,.2f} (Arquivo: {item['arquivo_origem'] or 'N/A'})\n"
        else:
            relatorio += "Nenhuma saída desacompanhada de documento foi detectada.\n"

        return relatorio


class SubagenteAuditorFinanceiro(Role):
    """Role do Subagente 1 no MetaGPT."""

    name: str = "Auditor_Financeiro"
    profile: str = "Auditor Contábil-Financeiro e Perito em Conciliação Bancária"
    goal: str = "Garantir conciliação de 100% das saídas de caixa e isolar todo centavo não comprovado."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([AuditarFinancasAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Iniciar auditoria")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    agent = SubagenteAuditorFinanceiro()
    res = await agent.run("Executar conciliação bancária completa")
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

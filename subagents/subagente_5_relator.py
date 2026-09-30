"""
Subagente 5: Relator de Auditoria e Orquestrador (MetaGPT Role)
Responsável por orquestrar todos os 4 subagentes especialistas, consolidar os achados
na Matriz de Severidade e gerar o Relatório Executivo Final de Auditoria.
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
from skills.matriz_severidade import SkillMatrizSeveridade
from subagents.subagente_1_financeiro import SubagenteAuditorFinanceiro
from subagents.subagente_2_conformidade import SubagenteAnalistaConformidade
from subagents.subagente_3_direito import SubagenteEspecialistaDireito
from subagents.subagente_4_contencioso import SubagenteConsultorContencioso


SYSTEM_PROMPT_RELATOR = """Você é o Subagente 5: Relator de Auditoria e Orquestrador Geral do condomínio 'Only Guillmon'.
Sua função é consolidar com rigor cartesiano e integridade pericial as análises de todos os subagentes.
Construa a Matriz de Severidade, calcule o impacto financeiro global e emita o parecer definitivo:
Aprovação, Aprovação com Ressalvas ou Rejeição das Contas com dever de ressarcimento.
"""


class EmitirRelatorioAuditoriaAction(Action):
    """Ação que orquestra os subagentes e gera o relatório executivo final."""

    name: str = "EmitirRelatorioAuditoriaAction"

    async def run(self, instrucao: str = "") -> str:
        print("\n[ORQUESTRADOR] Iniciando Pipeline Completo de Auditoria...")

        # 1. Executa Subagente 1 (Auditor Financeiro)
        print("  -> Executando Subagente 1 (Auditor Financeiro)...")
        a1 = SubagenteAuditorFinanceiro()
        res_a1 = await a1.run("Executar auditoria contábil")
        parecer_fin = res_a1.content

        # 2. Executa Subagente 2 (Analista de Conformidade)
        print("  -> Executando Subagente 2 (Analista de Conformidade)...")
        a2 = SubagenteAnalistaConformidade()
        res_a2 = await a2.run("Auditar conformidade de atas e quóruns")
        parecer_conf = res_a2.content

        # 3. Executa Subagente 3 (Direito Condominial)
        print("  -> Executando Subagente 3 (Direito Condominial - Notificação)...")
        a3 = SubagenteEspecialistaDireito()
        res_a3 = await a3.run("Gerar notificação formal de exibição")
        parecer_dir = res_a3.content

        # 4. Executa Subagente 4 (Consultor Contencioso)
        print("  -> Executando Subagente 4 (Consultor Contencioso - Ação Judicial)...")
        a4 = SubagenteConsultorContencioso()
        res_a4 = await a4.run("Gerar minuta de ação de exigir contas")
        parecer_cont = res_a4.content

        # 5. Consolidação e Emissão do Relatório pelo Relator
        print("  -> Consolidando Matriz de Severidade e emitindo Relatório Executivo...")
        sql = CondoAuditDatabase()
        skill_rel = SkillMatrizSeveridade(sql)
        relatorio_final = skill_rel.gerar_relatorio_executivo(
            parecer_financeiro=parecer_fin,
            parecer_conformidade=parecer_conf,
            parecer_direito=parecer_dir
        )

        return relatorio_final


class SubagenteRelatorOrquestrador(Role):
    """Role do Subagente 5 no MetaGPT."""

    name: str = "Relator_Auditoria_Orquestrador"
    profile: str = "Relator Geral de Auditoria e Orquestrador Multi-Agente"
    goal: str = "Consolidar todos os laudos periciais e emitir o relatório executivo final."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([EmitirRelatorioAuditoriaAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Emitir relatório")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    relator = SubagenteRelatorOrquestrador()
    res = await relator.run("Executar ciclo integral de auditoria")
    print("\n" + "="*80)
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

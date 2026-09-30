"""
Subagente 4: Consultor Jurídico-Contábil para Contencioso (MetaGPT Role)
Responsável por transformar os achados de auditoria em peças judiciais fundamentadas,
em especial a Ação de Exigir Contas (Art. 550 do CPC) e pareceres contenciosos.
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
from skills.gerador_pecas import SkillGeradorPecas


SYSTEM_PROMPT_CONTENCIOSO = """Você é o Subagente 4: Consultor Jurídico-Contábil para Contencioso do condomínio 'Only Guillmon'.
Sua função é converter todas as inconsistências financeiras graves e nulidades de assembleia em minutas de peças processuais judiciais (Ação de Exigir Contas - Art. 550 CPC).
Enquadre com precisão as teses de responsabilidade civil do síndico, gestão temerária e enriquecimento sem causa.
"""


class ElaborarPecaJudicialAction(Action):
    """Ação que redige a minuta da Ação de Exigir Contas."""

    name: str = "ElaborarPecaJudicialAction"

    async def run(self, instrucao: str = "") -> str:
        sql = CondoAuditDatabase()
        skill = SkillGeradorPecas(sql)

        minuta = skill.gerar_minuta_acao_exigir_contas(
            autor_nome="Ronaldo Akagui",
            reu_sindico="Síndico e Administradora do Condomínio Only Guillmon",
            comarca="São Paulo - Foro Regional correspondente"
        )

        return minuta


class SubagenteConsultorContencioso(Role):
    """Role do Subagente 4 no MetaGPT."""

    name: str = "Consultor_Juridico_Contencioso"
    profile: str = "Especialista em Contencioso Cível Condominial e Ação de Exigir Contas"
    goal: str = "Elaborar minutas e pareceres processuais que fundamentem judicialmente a restituição ao caixa."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ElaborarPecaJudicialAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Elaborar petição judicial")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    agent = SubagenteConsultorContencioso()
    res = await agent.run("Gerar minuta de ação de exigir contas")
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

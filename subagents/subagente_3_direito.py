"""
Subagente 3: Especialista em Direito Condominial e Imobiliário (MetaGPT Role)
Responsável por garantir o direito à informação analítica com base no Art. 1.348, VIII
e redigir a Notificação Extrajudicial de Exibição de Documentos com extratos bancários.
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
from tools.rag_engine import CondoRAGDatabase
from tools.sql_tool import CondoAuditDatabase
from skills.fundamentacao_analitica import SkillFundamentacaoAnalitica


SYSTEM_PROMPT_DIREITO = """Você é o Subagente 3: Especialista em Direito Condominial e Imobiliário do condomínio 'Only Guillmon'.
Sua função é fornecer a fundamentação jurídica irrefutável para que o condômino exija a exibição analítica de todos os extratos bancários e notas fiscais.
Baseie-se no Art. 1.348, VIII do Código Civil e na jurisprudência sedimentada do STJ que veda a prestação de contas meramente sintética.
Redija notificações de requerimento formal com advertência de Ação de Exigir Contas.
"""


class RequererDocumentacaoAction(Action):
    """Ação que redige a Notificação Extrajudicial de Exibição de Contas."""

    name: str = "RequererDocumentacaoAction"

    async def run(self, instrucao: str = "") -> str:
        rag = CondoRAGDatabase()
        sql = CondoAuditDatabase()
        skill = SkillFundamentacaoAnalitica(rag, sql)

        minuta = skill.gerar_notificacao_exibicao(
            nome_condomino="Ronaldo Akagui",
            unidade="Condômino Notificante - Only Guillmon"
        )

        return minuta


class SubagenteEspecialistaDireito(Role):
    """Role do Subagente 3 no MetaGPT."""

    name: str = "Especialista_Direito_Condominial"
    profile: str = "Consultor em Direito Condominial, Transparência e Exibição de Documentos"
    goal: str = "Blindar juridicamente o direito à exibição de contas analíticas e conciliação bancária integral."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([RequererDocumentacaoAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Requerer documentação analítica")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    agent = SubagenteEspecialistaDireito()
    res = await agent.run("Redigir notificação extrajudicial")
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

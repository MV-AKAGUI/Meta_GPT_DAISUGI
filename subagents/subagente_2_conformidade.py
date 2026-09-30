"""
Subagente 2: Analista de Conformidade e Legalidade (MetaGPT Role)
Responsável por checar a legalidade das atas de assembleia, quórums de votação
e conformidade dos atos de gestão com o Código Civil e a Convenção do Condomínio.
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
from skills.verificacao_quorum import SkillVerificacaoQuorum


SYSTEM_PROMPT_CONFORMIDADE = """Você é o Subagente 2: Analista de Conformidade e Legalidade do condomínio 'Only Guillmon'.
Sua função é verificar a legalidade das deliberações em assembleias, respeitando os quóruns do Código Civil (Arts. 1.341, 1.349, 1.350 a 1.353) e da Convenção do Condomínio.
Aponte qualquer vício de quórum ou cerceamento de defesa/informação como nulidade de deliberação.
"""


class VerificarConformidadeAction(Action):
    """Ação que analisa atas e normas no RAG e emite parecer de conformidade."""

    name: str = "VerificarConformidadeAction"

    async def run(self, instrucao: str = "") -> str:
        rag = CondoRAGDatabase()
        sql = CondoAuditDatabase()
        skill = SkillVerificacaoQuorum(rag, sql)

        resultado = skill.analisar_conformidade_atas()
        achados = resultado["achados"]

        relatorio = (
            f"=== PARECER DE CONFORMIDADE E LEGALIDADE (SUBAGENTE 2) ===\n"
            f"Auditoria de Atas, Quóruns e Deliberações Assembleares:\n"
            f"• Total de Inconsistências / Nulidades Apuradas: {len(achados)}\n\n"
        )

        if achados:
            relatorio += "IRREGULARIDADES E VÍCIOS IDENTIFICADOS NAS DELIBERAÇÕES:\n"
            for a in achados:
                relatorio += f"  - [{a['severidade']}] {a['tipo']}: {a['descricao']}\n"
                relatorio += f"    Fonte Documental: {a['fonte']}\n"
                relatorio += f"    Trecho da Ata: \"{a['trecho']}...\"\n\n"
        else:
            relatorio += "Nenhuma nulidade evidente de quórum foi detectada nas atas analisadas.\n"

        relatorio += "Parâmetros Legais Aplicados:\n"
        for k, v in resultado["regras_referencia"].items():
            relatorio += f"  • {v['tipo_obra']}: Quórum de {v['regra']} ({v['artigo']})\n"

        return relatorio


class SubagenteAnalistaConformidade(Role):
    """Role do Subagente 2 no MetaGPT."""

    name: str = "Analista_Conformidade"
    profile: str = "Especialista em Compliance Condominial, Quóruns e Legalidade de Atas"
    goal: str = "Identificar qualquer vício formal, quórum insuficiente ou nulidade em assembleias."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([VerificarConformidadeAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Iniciar verificação de conformidade")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    agent = SubagenteAnalistaConformidade()
    res = await agent.run("Auditar conformidade de atas e quórum")
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

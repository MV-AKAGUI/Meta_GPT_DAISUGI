"""
Subagente 0: Agente de Triagem e Mineração Documental (MetaGPT Role)
Responsável por varrer '00_Documentos_In_Natura', processar via Docling,
classificar semanticamente e despachar os arquivos para as pastas canônicas no Drive.
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
from tools.doc_triage import DocumentTriageEngine, compute_file_hash
from config.drive_paths import IN_NATURA, verify_drive_integrity


SYSTEM_PROMPT_TRIAGEM = """Você é o Subagente 0: Auditor de Triagem e Mineração Documental do condomínio 'Only Guillmon'.
Sua missão primordial é inspecionar todos os arquivos depositados na pasta '00_Documentos_In_Natura', analisar o conteúdo extraído pelo Docling, identificar o tipo de documento, competência temporal e despachá-lo com 100% de rastreabilidade para uma das pastas canônicas:
- 01_Atas_e_Assembleias
- 02_Extratos_Bancarios
- 03_Notas_Fiscais_e_Recibos
- 04_Convencao_e_Regulamento
- 05_Previsao_Orcamentaria
Se o documento for ambíguo ou de baixa confiança, envie para '99_Revisao_Pendente'.
Gere sempre o manifesto em formato auditável com hash SHA256 e justificativa da classificação.
"""


class TriarDocumentosAction(Action):
    """Ação que executa a varredura, extração Docling e despacho documental."""

    name: str = "TriarDocumentosAction"

    async def run(self, instrucao: str = "") -> str:
        engine = DocumentTriageEngine()
        manifest = engine.run_triage_batch()

        total = manifest["total_arquivos"]
        processados = len(manifest["processados"])
        erros = len(manifest["erros"])

        resumo = (
            f"Relatório de Triagem Documental:\n"
            f"- Total de arquivos encontrados em In Natura: {total}\n"
            f"- Processados e distribuídos com sucesso: {processados}\n"
            f"- Arquivos com erro ou pendência: {erros}\n"
        )
        if manifest["processados"]:
            resumo += "\nDistribuição realizada:\n"
            for item in manifest["processados"]:
                resumo += f"  • {item['nome_original']} -> [{item['categoria']}] {item['nome_destino']}\n"

        return resumo


class SubagenteTriagem(Role):
    """Role do Subagente 0 no MetaGPT."""

    name: str = "Auditor_Triagem_In_Natura"
    profile: str = "Especialista em Triagem, Mineração Documental e Rastreabilidade"
    goal: str = "Classificar e distribuir com 100% de precisão e segurança os arquivos da pasta In Natura para as pastas canônicas."

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([TriarDocumentosAction])
        self._set_react_mode(react_mode="by_order")

    async def _act(self) -> Message:
        todo = self.rc.todo
        msg = self.get_memories(k=1)[0] if self.get_memories() else Message(content="Iniciar triagem")
        result = await todo.run(msg.content)
        msg_result = Message(content=result, role=self.profile, cause_by=type(todo))
        self.rc.memory.add(msg_result)
        return msg_result


async def main():
    agent = SubagenteTriagem()
    res = await agent.run("Efetuar triagem da pasta 00_Documentos_In_Natura")
    print(res.content)


if __name__ == "__main__":
    asyncio.run(main())

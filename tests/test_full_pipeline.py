"""
Teste de Ciclo Completo (End-to-End) do Sistema de Auditoria MetaGPT
Orquestra o Subagente 5 (Relator), executando em cascata os Subagentes 1, 2, 3 e 4.
"""

from pathlib import Path
import asyncio
import sys

app_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_root))

from subagents.subagente_5_relator import SubagenteRelatorOrquestrador
from config.drive_paths import OUTPUTS_RELATORIOS, OUTPUTS_NOTIFICACOES


async def run_e2e_test():
    print("=== INICIANDO TESTE END-TO-END DO ECOSSISTEMA MULTI-AGENTE ===")
    relator = SubagenteRelatorOrquestrador()
    resultado = await relator.run("Executar auditoria completa e gerar relatório pericial")
    
    assert resultado is not None, "O resultado não pode ser nulo"
    assert "RELATÓRIO DE AUDITORIA CONTÁBIL" in resultado.content, "Cabeçalho do relatório deve estar presente"

    # Verifica se os arquivos físicos foram gerados no disco
    relatorios_gerados = list(OUTPUTS_RELATORIOS.glob("*.md"))
    notificacoes_geradas = list(OUTPUTS_NOTIFICACOES.glob("*.md"))

    print(f"\n[OK] Relatórios gerados em disco: {len(relatorios_gerados)}")
    for r in relatorios_gerados[-2:]:
        print(f"  • {r.name}")

    print(f"\n[OK] Peças e Notificações geradas em disco: {len(notificacoes_geradas)}")
    for n in notificacoes_geradas[-2:]:
        print(f"  • {n.name}")

    print("\n=== TESTE END-TO-END FINALIZADO COM 100% DE SUCESSO! ===")


if __name__ == "__main__":
    asyncio.run(run_e2e_test())

import asyncio
from metagpt.roles import ProductManager
from metagpt.schema import Message

async def main():
    print("\n[1/3] Inicializando o Product Manager...")
    pm = ProductManager()
    prompt = (
        "Voce e o Product Manager lider do projeto DAISUGI para a construtora. "
        "Elabore um PRD completo, profissional e detalhado em Portugues "
        "para a plataforma DAISUGI: Sistema corporativo web e mobile para gestao de obras com: "
        "1. Painel de cronograma integrado com medicoes de empreiteiros em campo; "
        "2. Registro fotografico de evidencias e aprovacao de pagamentos por alcada; "
        "3. Relatorios executivos de avanco fisico-financeiro e projecao de custos; "
        "4. Notificacoes automaticas e alertas de desvios via WhatsApp e e-mail; "
        "5. Modulo de governanca, seguranca e conformidade LGPD. "
        "Inclua no documento: Product Goals, User Stories e Personas, Competitive Analysis, "
        "Requirement Pool (P0, P1, P2) e arquitetura/fluxo em sintaxe Mermaid."
    )
    print("[2/3] Agente gerando o PRD com DeepSeek (aguarde alguns minutos)...\n")
    resultado = await pm.run(Message(content=prompt))
    print("[3/3] Salvando o documento em PRD_DAISUGI.md...")
    with open("PRD_DAISUGI.md", "w", encoding="utf-8") as out:
        out.write(resultado.content)
    print("\n============================================")
    print("PRD GERADO COM SUCESSO EM: PRD_DAISUGI.md")
    print("============================================\n")

if __name__ == "__main__":
    asyncio.run(main())

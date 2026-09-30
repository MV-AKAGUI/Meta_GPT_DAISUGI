import asyncio
from metagpt.roles import ProductManager
from metagpt.schema import Message

async def main():
    pm = ProductManager()
    resultado = await pm.run(Message(content="Qual o papel de um Product Manager? Responda em 1 frase curta."))
    print("RESPOSTA DA IA:", resultado.content)

if __name__ == "__main__":
    asyncio.run(main())

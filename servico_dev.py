import hmac
import os
import re
import time
from typing import Dict, List, Optional
from fastapi import FastAPI, Header, HTTPException
import httpx
from pydantic import BaseModel

METAGPT_DEV_TOKEN = os.environ.get("METAGPT_DEV_TOKEN")
if not METAGPT_DEV_TOKEN:
    raise RuntimeError("METAGPT_DEV_TOKEN não configurada no ambiente")

app = FastAPI(title="MetaGPT Dev Service", version="1.0.0")

OLLAMA_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
MODELO_PADRAO = "qwen2.5-coder:7b"

SYSTEM_PROMPT = """Você é o MetaGPT Dev, engenheiro de software autônomo do ecossistema DAISUGI.
Sua missão é gerar código Python de alta qualidade, modular, seguro e limpo para atender à requisição do usuário.
Responda sempre incluindo os blocos de código com a identificação do caminho relativo do arquivo no formato:
```python # caminho: nome_do_arquivo.py
<conteudo do codigo>
```
Não adicione explicações desnecessárias fora dos blocos de código."""


class GerarCodigoRequest(BaseModel):
    requisicao: str
    contexto: Optional[str] = None
    missao_id: Optional[str] = None


def extrair_arquivos(texto: str) -> List[Dict[str, str]]:
    padrao = re.compile(
        r"```(?:python)?(?:\s*#\s*caminho:\s*([^\r\n]+))?\r?\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    matches = padrao.findall(texto)
    arquivos: List[Dict[str, str]] = []
    idx = 1
    for caminho_match, codigo in matches:
        caminho = caminho_match.strip() if caminho_match and caminho_match.strip() else f"modulo_{idx}.py"
        conteudo = codigo.strip()
        if conteudo:
            arquivos.append({"caminho": caminho, "conteudo": conteudo})
            idx += 1
    return arquivos


@app.get("/health")
def health():
    return {
        "status": "ok",
        "servico": "metagpt-dev",
        "modelo": MODELO_PADRAO,
    }


@app.post("/gerar-codigo")
async def gerar_codigo_endpoint(
    corpo: GerarCodigoRequest,
    x_metagpt_token: Optional[str] = Header(None, alias="X-MetaGPT-Token"),
):
    token_esperado = os.environ.get("METAGPT_DEV_TOKEN", "")
    if not token_esperado or not x_metagpt_token or not hmac.compare_digest(
        x_metagpt_token, token_esperado
    ):
        raise HTTPException(
            status_code=401, detail="Token ausente ou invalido"
        )

    inicio = time.time()
    conteudo_usuario = (
        f"Demanda: {corpo.requisicao}\nContexto: {corpo.contexto}"
        if corpo.contexto
        else f"Demanda: {corpo.requisicao}"
    )

    payload = {
        "model": MODELO_PADRAO,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": conteudo_usuario},
        ],
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/v1/chat/completions", json=payload
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Erro no provedor Ollama: {resp.status_code}",
                )
            data = resp.json()
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Falha de comunicação com Ollama: {type(e).__name__}",
        )

    duracao = round(time.time() - inicio, 2)
    escolhas = data.get("choices", [])
    texto_resposta = (
        escolhas[0].get("message", {}).get("content", "") if escolhas else ""
    )
    modelo_retornado = data.get("model", MODELO_PADRAO)

    arquivos = extrair_arquivos(texto_resposta)

    return {
        "arquivos": arquivos,
        "modelo": modelo_retornado,
        "duracao_s": duracao,
    }


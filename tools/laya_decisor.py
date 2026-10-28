"""Cliente único do Laya (decisões com probabilidade calibrada) para todo o ecossistema DAISUGI.

Arquivo canônico: FERRAMENTAS--FUZZY---HARNESS-/ferramentas/laya_decisor.py (versão 1).
Cópias idênticas vivem em outros repos (Dai_Smart, Meta_GPT); ao mudar aqui, copie para lá.
Só biblioteca padrão: qualquer app usa sem instalar torch. O modelo roda no serviço laya_service/.

Modos (LAYA_MODO, ou LAYA_MODO_<PONTO> para um ponto só, ex.: LAYA_MODO_METAGPT_TRIAGEM=ativo):
  desligado (padrão) nada é chamado; o app segue 100% no caminho atual.
  sombra             o app decide como sempre e o Laya decide em paralelo, só para registro
                     (zero impacto na resposta; gera o dataset do fine-tune e a comparação).
  ativo              o Laya decide primeiro; se a confiança >= LAYA_LIMIAR (padrão 0.9) o app usa a
                     escolha dele, senão segue no caminho atual (LLM, regra ou fuzzy). Ligar por ponto
                     só depois que evals/promover.py aprovar.

Uso no app (os dois lados juntos):
    escolha = laya_decisor.escolher(PONTO, texto, opcoes, instrucao)      # só age no modo ativo
    if escolha is None:
        escolha = caminho_atual(texto)
        laya_decisor.sombra_escolha(PONTO, texto, opcoes, instrucao, escolha)  # só age no modo sombra

Outras variáveis: LAYA_URL (padrão http://127.0.0.1:8095), LAYA_API_KEY (cofre Infisical),
LAYA_MODELO_<PONTO> (checkpoint de fine-tune registrado no serviço, ex.: LAYA_MODELO_FERRAMENTAS_ROTEADOR=roteador-v1),
LAYA_LOG_DIR (padrão ~/.daisugi/laya_sombra; fora dos repos porque guarda o texto dos pedidos).
"""
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

_TIMEOUT_S = 3.0


def modo(ponto: str) -> str:
    chave = "LAYA_MODO_" + "".join(c if c.isalnum() else "_" for c in ponto).upper()
    return (os.getenv(chave) or os.getenv("LAYA_MODO") or "desligado").strip().lower()


def _limiar() -> float:
    return float(os.getenv("LAYA_LIMIAR", "0.9"))


def _modelo(ponto: str) -> str:
    """Checkpoint do ponto: LAYA_MODELO_<PONTO> (um fine-tune registrado no serviço) ou o multilíngue base."""
    chave = "LAYA_MODELO_" + "".join(c if c.isalnum() else "_" for c in ponto).upper()
    return os.getenv(chave) or "multilingual"


def _consultar(ponto: str, texto: str, perguntas: dict) -> dict:
    req = urllib.request.Request(
        os.getenv("LAYA_URL", "http://127.0.0.1:8095") + "/v1/systemone",
        data=json.dumps({"state": texto, "questions": perguntas, "model": _modelo(ponto)}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.getenv("LAYA_API_KEY", "")},
    )
    # sombra roda em segundo plano e pode esperar o carregamento lazy de um fine-tune; o modo ativo não pode
    with urllib.request.urlopen(req, timeout=30 if modo(ponto) == "sombra" else _TIMEOUT_S) as r:
        return json.load(r)["answers"]


def _registrar(ponto: str, registro: dict) -> None:
    try:
        pasta = Path(os.getenv("LAYA_LOG_DIR") or Path.home() / ".daisugi" / "laya_sombra")
        pasta.mkdir(parents=True, exist_ok=True)
        with open(pasta / f"{ponto}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _decidir(ponto: str, texto: str, perguntas: dict, decisao_atual=None) -> dict:
    """Consulta o Laya e registra. Nunca levanta exceção: Laya fora do ar não derruba o app."""
    t0 = time.perf_counter()
    try:
        resposta, erro = _consultar(ponto, texto, perguntas).get("decisao") or {}, None
    except Exception as e:
        resposta, erro = {}, f"{type(e).__name__}: {e}"[:200]
    _registrar(ponto, {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "ponto": ponto,
        "modo": modo(ponto),
        "modelo": _modelo(ponto),
        "texto": texto,
        "decisao_atual": decisao_atual,
        "laya": {k: resposta.get(k) for k in ("choice", "noul", "confidence", "probabilities")},
        "ms": round((time.perf_counter() - t0) * 1000),
        "erro": erro,
    })
    return resposta


def _pergunta_escolha(opcoes: dict, instrucao: str) -> dict:
    return {"decisao": {"type": "choice", "instructions": instrucao, "criteria": opcoes}}


def _pergunta_noul(instrucao: str) -> dict:
    return {"decisao": {"type": "noul", "instructions": instrucao}}


def escolher(ponto: str, texto: str, opcoes: dict, instrucao: str):
    """Modo ativo: devolve a opção do Laya se confiante, senão None. Outros modos: None, sem chamar nada."""
    if modo(ponto) != "ativo":
        return None
    r = _decidir(ponto, texto, _pergunta_escolha(opcoes, instrucao))
    return r.get("choice") if (r.get("confidence") or 0) >= _limiar() else None


def sim_ou_nao(ponto: str, texto: str, instrucao: str):
    """Modo ativo: True/False se o Laya estiver confiante, senão None. Outros modos: None."""
    if modo(ponto) != "ativo":
        return None
    p = _decidir(ponto, texto, _pergunta_noul(instrucao)).get("noul")
    if p is None:
        return None
    return True if p >= _limiar() else False if p <= 1 - _limiar() else None


def sombra_escolha(ponto: str, texto: str, opcoes: dict, instrucao: str, decisao_atual) -> None:
    """Modo sombra: registra em segundo plano o que o Laya escolheria ao lado da decisão atual."""
    if modo(ponto) == "sombra":
        threading.Thread(target=_decidir, args=(ponto, texto, _pergunta_escolha(opcoes, instrucao), decisao_atual), daemon=True).start()


def sombra_sim_ou_nao(ponto: str, texto: str, instrucao: str, decisao_atual) -> None:
    """Modo sombra: registra em segundo plano a resposta sim/não do Laya ao lado da decisão atual."""
    if modo(ponto) == "sombra":
        threading.Thread(target=_decidir, args=(ponto, texto, _pergunta_noul(instrucao), decisao_atual), daemon=True).start()

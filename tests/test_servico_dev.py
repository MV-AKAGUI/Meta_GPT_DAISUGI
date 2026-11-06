import os
import sys
import pytest
from fastapi.testclient import TestClient

TOKEN_TESTE = "token_de_teste_seguro_123456"

def test_falha_sem_token_no_ambiente(monkeypatch):
    monkeypatch.delenv("METAGPT_DEV_TOKEN", raising=False)
    if "servico_dev" in sys.modules:
        del sys.modules["servico_dev"]
    with pytest.raises(RuntimeError) as exc_info:
        import servico_dev
    assert "METAGPT_DEV_TOKEN não configurada" in str(exc_info.value)


def test_health_endpoint(monkeypatch):
    monkeypatch.setenv("METAGPT_DEV_TOKEN", TOKEN_TESTE)
    if "servico_dev" in sys.modules:
        del sys.modules["servico_dev"]
    import servico_dev
    client = TestClient(servico_dev.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["servico"] == "metagpt-dev"
    assert data["modelo"] == "qwen2.5-coder:7b"


def test_gerar_codigo_sem_header(monkeypatch):
    monkeypatch.setenv("METAGPT_DEV_TOKEN", TOKEN_TESTE)
    if "servico_dev" in sys.modules:
        del sys.modules["servico_dev"]
    import servico_dev
    client = TestClient(servico_dev.app)
    resp = client.post("/gerar-codigo", json={"requisicao": "criar calculadora"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token ausente ou invalido"


def test_gerar_codigo_token_errado(monkeypatch):
    monkeypatch.setenv("METAGPT_DEV_TOKEN", TOKEN_TESTE)
    if "servico_dev" in sys.modules:
        del sys.modules["servico_dev"]
    import servico_dev
    client = TestClient(servico_dev.app)
    resp = client.post(
        "/gerar-codigo",
        json={"requisicao": "criar calculadora"},
        headers={"X-MetaGPT-Token": "token_incorreto"}
    )
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Token ausente ou invalido"

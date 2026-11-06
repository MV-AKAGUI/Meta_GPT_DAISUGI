#!/usr/bin/env python3
"""
Meta_GPT_DAISUGI v2.0 - Gerador Automático de SDD, C4, Prisma Schema e Código
Especialista em SUGOI_CADEIA_DE_VALOR e projetos de processos BPM/HAP/EAP.
Sob Framework A: integrado diretamente ao serviço local S1 (metagpt-dev) na porta 8002.

Uso:
  python main.py --spec <BRIEFING.md> --project <NOME_PROJETO> --output <DIRETÓRIO>
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

S1_URL = os.getenv("METAGPT_DEV_URL", "http://127.0.0.1:8002").rstrip("/")


def _obter_token() -> str:
    token = os.environ.get("METAGPT_DEV_TOKEN", "")
    if not token:
        try:
            import subprocess
            res = subprocess.run(
                ["infisical", "secrets", "get", "METAGPT_DEV_TOKEN", "--plain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if res.returncode == 0 and res.stdout.strip():
                token = res.stdout.strip()
        except Exception:
            pass
    return token


def run_generation(spec_path: str, project_name: str, output_dir: str):
    """
    Executa geração de código e especificações através do serviço S1 do MetaGPT.
    """
    print("\n" + "="*80)
    print(f"🚀 META_GPT_DAISUGI (Framework A - S1)")
    print(f"   Projeto: {project_name}")
    print(f"   Briefing: {spec_path}")
    print(f"   Output: {output_dir}")
    print(f"   Endpoint: {S1_URL}")
    print("="*80)

    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"❌ ERRO: Briefing não encontrado: {spec_path}")
        sys.exit(1)

    conteudo_spec = spec_file.read_text(encoding="utf-8")
    print(f"\n✅ Briefing carregado com sucesso ({len(conteudo_spec)} caracteres)")

    token = _obter_token()
    if not token:
        print("❌ ERRO: METAGPT_DEV_TOKEN não configurada no ambiente nem no Infisical.")
        sys.exit(1)

    print(f"\n📌 Disparando geração via serviço metagpt-dev...")
    payload = {
        "requisicao": f"Projeto {project_name}: Gerar SDD, C4 Diagrams e código modular para atender à especificação.",
        "contexto": conteudo_spec[:4000],
        "missao_id": None
    }

    req_data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "X-MetaGPT-Token": token
    }

    req = urllib.request.Request(f"{S1_URL}/gerar-codigo", data=req_data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                arquivos = data.get("arquivos", [])
                modelo = data.get("modelo")
                duracao = data.get("duracao_s")

                out_path = Path(output_dir)
                out_path.mkdir(parents=True, exist_ok=True)

                for arq in arquivos:
                    caminho_rel = arq.get("caminho", "output.txt")
                    conteudo = arq.get("conteudo", "")
                    dest = out_path / caminho_rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(conteudo, encoding="utf-8")
                    print(f"   ✓ Arquivo gerado: {dest.name} ({len(conteudo)} bytes)")

                print(f"\n✅ Meta_GPT concluído com sucesso!")
                print(f"   Modelo utilizado: {modelo}")
                print(f"   Duração: {duracao}s")
                print(f"   Total de arquivos salvos em: {output_dir}")
            else:
                print(f"❌ ERRO: S1 retornou HTTP {resp.status}")
                sys.exit(1)
    except urllib.error.HTTPError as e:
        print(f"❌ ERRO HTTP ao chamar S1 ({e.code}): {e.read().decode('utf-8', errors='ignore')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERRO de comunicação com S1: {e}")
        sys.exit(1)

    print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Meta_GPT_DAISUGI - Gerador de SDD, C4 e Artefatos de Código",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Caminho para o briefing / especificação em markdown"
    )

    parser.add_argument(
        "--project",
        default="SUGOI_PROJETO",
        help="Nome do projeto (ex: SUGOI_Cadeia_Valor_FASE1)"
    )

    parser.add_argument(
        "--output",
        default="./output/fase1_autogen",
        help="Diretório de saída para salvar os artefatos gerados"
    )

    args = parser.parse_args()
    run_generation(args.spec, args.project, args.output)


if __name__ == "__main__":
    main()

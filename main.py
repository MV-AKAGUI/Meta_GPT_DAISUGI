#!/usr/bin/env python3
"""
Meta_GPT_DAISUGI v2.0 - Gerador Automático de SDD, C4, Prisma Schema
Especialista em SUGOI_CADEIA_DE_VALOR e projetos de processos BPM/HAP/EAP

Uso:
  python main.py --spec <BRIEFING.md> --project <NOME_PROJETO> --output <DIRETÓRIO>
"""

import sys
import argparse
from pathlib import Path

# Adiciona o diretório da aplicação ao sys.path
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def run_generation(spec_path: str, project_name: str, output_dir: str):
    """
    Executa Meta_GPT para gerar SDD, C4, Prisma schema automaticamente.

    Args:
        spec_path: Caminho para o arquivo de briefing (FASE_1_OTIMIZADA.md)
        project_name: Nome do projeto (ex: SUGOI_Cadeia_Valor_FASE1)
        output_dir: Diretório onde salvar outputs
    """
    print("\n" + "="*80)
    print(f"🚀 META_GPT_DAISUGI v2.0")
    print(f"   Projeto: {project_name}")
    print(f"   Briefing: {spec_path}")
    print(f"   Output: {output_dir}")
    print("="*80)

    spec_file = Path(spec_path)
    if not spec_file.exists():
        print(f"❌ ERRO: Briefing não encontrado: {spec_path}")
        sys.exit(1)

    print(f"\n✅ Briefing validado ({spec_file.stat().st_size} bytes)")

    # Executar Meta_GPT
    print(f"\n📌 Iniciando geração Meta_GPT...")
    print(f"   Comando: metagpt --project {project_name} --spec {spec_path} --output {output_dir}")

    import subprocess

    cmd = [
        "metagpt",
        "--project", project_name,
        "--spec", spec_path,
        "--output", output_dir
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ Meta_GPT concluído com sucesso!")
        print(f"\n📂 Outputs gerados em: {output_dir}")
        print(f"   ✓ SDD_AUTOGEN.md (500+ linhas)")
        print(f"   ✓ C4_DIAGRAMS.md (Mermaid)")
        print(f"   ✓ prisma/schema.prisma")
        print(f"   ✓ tests/sample.test.ts")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ ERRO ao executar Meta_GPT: {e}")
        print(f"\n💡 Fallback: Gerar schema manualmente")
        print(f"   prisma init")
        sys.exit(1)

    print("\n" + "="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Meta_GPT_DAISUGI v2.0 - Gerador de SDD, C4, Prisma Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:

  # Para SUGOI_CADEIA_DE_VALOR FASE 1
  python main.py \\
    --spec ../.claude/FASE_1_OTIMIZADA.md \\
    --project SUGOI_Cadeia_Valor_FASE1 \\
    --output ./output/fase1_autogen/

  # Ou via metagpt diretamente:
  metagpt --project SUGOI_Cadeia_Valor_FASE1 \\
    --spec FASE_1_OTIMIZADA.md \\
    --output output/fase1_autogen/
        """
    )

    parser.add_argument(
        "--spec",
        required=True,
        help="Caminho para arquivo de briefing (FASE_1_OTIMIZADA.md)"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="Nome do projeto (ex: SUGOI_Cadeia_Valor_FASE1)"
    )
    parser.add_argument(
        "--output",
        default="./output/autogen/",
        help="Diretório de saída (default: ./output/autogen/)"
    )

    args = parser.parse_args()

    run_generation(args.spec, args.project, args.output)


if __name__ == "__main__":
    main()

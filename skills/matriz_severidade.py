"""
Skill: Matriz de Severidade e Síntese Executiva de Auditoria
Utilizada pelo Subagente 5 (Relator de Auditoria e Orquestrador)
Consolida todos os achados dos Subagentes 1, 2, 3 e 4, calcula os níveis de gravidade
e emite a recomendação pericial (Aprovação / Ressalvas / Rejeição das Contas).
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.sql_tool import CondoAuditDatabase
from config.drive_paths import OUTPUTS_RELATORIOS


class SkillMatrizSeveridade:
    """Calcula a matriz de risco e emite o parecer executivo final de auditoria."""

    def __init__(self, sql_db: CondoAuditDatabase):
        self.sql = sql_db

    def consolidar_matriz_risco(self) -> Dict[str, Any]:
        """Agrupa e quantifica as inconsistências catalogadas."""
        conn = self.sql.get_connection()
        todas = conn.execute("""
            SELECT id, data_ocorrencia, tipo_inconsistencia, grau_severidade,
                   valor_envolvido, descricao_detalhada, subagente_origem
            FROM inconsistencias_auditoria
            ORDER BY grau_severidade DESC, data_ocorrencia ASC
        """).fetchall()

        graves = [dict(r) for r in todas if r["grau_severidade"] == "GRAVE"]
        medios = [dict(r) for r in todas if r["grau_severidade"] == "MEDIO"]
        leves = [dict(r) for r in todas if r["grau_severidade"] == "LEVE"]

        total_impacto_grave = sum(r["valor_envolvido"] for r in graves)
        total_impacto_medio = sum(r["valor_envolvido"] for r in medios)

        # Regra decisória da recomendação pericial
        if graves or total_impacto_grave > 500.0:
            recomendacao = "REJEIÇÃO INTEGRAL DAS CONTAS (COM DEVER DE RESSARCIMENTO)"
            status_cor = "CRÍTICO / VERMELHO"
        elif medios or total_impacto_medio > 1000.0:
            recomendacao = "APROVAÇÃO COM RESSALVAS GRAVES E EXIGÊNCIA DE SANEAMENTO"
            status_cor = "ALERTA / AMARELO"
        else:
            recomendacao = "APROVAÇÃO REGULAR DAS CONTAS"
            status_cor = "REGULAR / VERDE"

        return {
            "recomendacao_final": recomendacao,
            "status_cor": status_cor,
            "total_inconsistencias": len(todas),
            "qtd_graves": len(graves),
            "qtd_medios": len(medios),
            "qtd_leves": len(leves),
            "impacto_financeiro_grave": round(total_impacto_grave, 2),
            "impacto_financeiro_medio": round(total_impacto_medio, 2),
            "achados_graves": graves,
            "achados_medios": medios,
            "achados_leves": leves
        }

    def gerar_relatorio_executivo(
        self,
        parecer_financeiro: str = "",
        parecer_conformidade: str = "",
        parecer_direito: str = ""
    ) -> str:
        """Gera o documento final de auditoria em Markdown rico e salva em outputs/relatorios/."""
        matriz = self.consolidar_matriz_risco()
        data_relatorio = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

        tabela_graves = ""
        for g in matriz["achados_graves"]:
            tabela_graves += f"| {g['data_ocorrencia']} | **{g['tipo_inconsistencia']}** | R$ {g['valor_envolvido']:,.2f} | {g['descricao_detalhada']} | {g['subagente_origem']} |\n"

        if not tabela_graves:
            tabela_graves = "| N/A | Nenhuma irregularidade grave | R$ 0,00 | Regular | Sistema |\n"

        md_content = f"""# RELATÓRIO DE AUDITORIA CONTÁBIL E CONFORMIDADE JURÍDICA
**Condomínio Only Guillmon**  
*Data de Emissão:* {data_relatorio}  
*Metodologia:* Sistema Multi-Agente Autônomo com MetaGPT, Docling e LangChain

---

## 1. PARECER CONCLUSIVO DO RELATOR

> **RECOMENDAÇÃO TÉCNICO-PERICIAL:**  
> ### **{matriz['recomendacao_final']}**  
> **Nível de Criticidade da Gestão:** `{matriz['status_cor']}`

### Resumo dos Indicadores de Risco:
* **Total de Fatos Apurados:** {matriz['total_inconsistencias']}
* **Apontamentos Graves:** {matriz['qtd_graves']} (Impacto Financeiro Apurado: **R$ {matriz['impacto_financeiro_grave']:,.2f}**)
* **Apontamentos Médios:** {matriz['qtd_medios']} (Impacto: **R$ {matriz['impacto_financeiro_medio']:,.2f}**)
* **Apontamentos Leves:** {matriz['qtd_leves']}

---

## 2. MATRIZ DE SEVERIDADE DOS ACHADOS

| Data | Tipo de Inconsistência | Impacto Financeiro | Descrição Circunstanciada | Origem Pericial |
| :--- | :--- | :--- | :--- | :--- |
{tabela_graves}

---

## 3. SÍNTESE DA AUDITORIA FINANCEIRA (SUBAGENTE 1)
```text
{parecer_financeiro.strip()}
```

---

## 4. SÍNTESE DA CONFORMIDADE E QUÓRUMS (SUBAGENTE 2)
```text
{parecer_conformidade.strip()}
```

---

## 5. ENQUADRAMENTO JURÍDICO E MEDIDAS RECOMENDADAS (SUBAGENTE 3 E 4)
1. **Notificação Extrajudicial Interpelatória:** Concessão de prazo improrrogável de 10 dias úteis para que o(a) síndico(a) apresente cópia integral dos extratos bancários de todas as contas e comprovantes das saídas não justificadas.
2. **Ação de Exigir Contas (Art. 550 CPC):** Em caso de inércia ou recusa, propositura imediata perante o foro competente para apuração judicial do saldo credor em favor do condomínio.
3. **Representação por Gestão Temerária:** Responsabilização civil pessoal pelos valores despendidos sem respaldo assemblear ou comprovação contábil (Art. 186 e 927 do Código Civil).

---
*Relatório emitido e chancelado pelo Subagente 5 (Relator de Auditoria e Orquestrador).*
"""
        OUTPUTS_RELATORIOS.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        relatorio_path = OUTPUTS_RELATORIOS / f"Relatorio_Auditoria_Condo_Only_Guillmon_{timestamp}.md"
        relatorio_path.write_text(md_content, encoding="utf-8")
        print(f"[Relatório Salvo] {relatorio_path}")

        return md_content

"""
Skill: Gerador de Peças Processuais e Pareceres Contenciosos
Utilizada pelo Subagente 4 (Consultor Jurídico-Contábil para Contencioso)
Elabora minutas de petições iniciais (Ação de Exigir Contas - Art. 550 CPC) e pareceres de responsabilização civil/criminal.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.sql_tool import CondoAuditDatabase
from config.drive_paths import OUTPUTS_NOTIFICACOES


class SkillGeradorPecas:
    """Transforma os achados contábeis e de conformidade em peças processuais estruturadas."""

    def __init__(self, sql_db: CondoAuditDatabase):
        self.sql = sql_db

    def gerar_minuta_acao_exigir_contas(
        self,
        autor_nome: str = "Ronaldo Akagui",
        reu_sindico: str = "Administração / Síndico em Exercício",
        comarca: str = "São Paulo - SP"
    ) -> str:
        """
        Gera a minuta completa da petição inicial da Ação de Exigir Contas (Art. 550 CPC).
        """
        # Coleta inconsistências graves gravadas no SQLite
        conn = self.sql.get_connection()
        achados_graves = conn.execute("""
            SELECT data_ocorrencia, tipo_inconsistencia, valor_envolvido, descricao_detalhada
            FROM inconsistencias_auditoria
            WHERE grau_severidade = 'GRAVE'
            ORDER BY data_ocorrencia ASC
        """).fetchall()

        total_desvios = sum(a["valor_envolvido"] for a in achados_graves)
        lista_achados_str = ""
        for a in achados_graves:
            lista_achados_str += f"  • Data: {a['data_ocorrencia']} | Valor: R$ {a['valor_envolvido']:,.2f} | Fato: {a['descricao_detalhada']}\n"

        if not lista_achados_str:
            lista_achados_str = "  • Ausência de extratos bancários conciliados e recusa de prestação de contas analítica.\n"

        minuta_judicial = f"""
EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DE UMA DAS VARAS CÍVEIS DO FORO DA COMARCA DE {comarca.upper()}

AUTOR: {autor_nome}, brasileiro, condômino e legítimo proprietário de unidade no Condomínio Only Guillmon.
RÉU: {reu_sindico}, na qualidade de gestor(a) e administrador(a) dos recursos comuns do Condomínio Only Guillmon.

AÇÃO DE EXIGIR CONTAS
(Com fulcro no Artigo 550 e seguintes do Código de Processo Civil c/c Artigo 1.348, VIII do Código Civil)

I - DOS FATOS E DO INTERESSE DE AGIR
O Autor é condômino do Condomínio Only Guillmon e vem, reiteradamente, solicitando acesso à prestação de contas em sua modalidade analítica e mercantil, instruída com os extratos bancários de todas as contas do condomínio e as correspondentes notas fiscais.
Não obstante o dever legal imposto pelo Artigo 1.348, VIII do CC, a gestão tem se recusado ou apresentado balancetes meramente sintéticos, ocultando a destinação real das verbas condominiais.

II - DAS IRREGULARIDADES E INCONSISTÊNCIAS APURADAS PRELIMINARMENTE
Em procedimento de auditoria técnica local, foram identificados os seguintes fatos graves que justificam a intervenção do Poder Judiciário:
{lista_achados_str}
Montante preliminar sob suspeita / sem comprovação formal: R$ {total_desvios:,.2f}.

III - DO DIREITO (ART. 550 DO CPC E JURISPRUDÊNCIA DO STJ)
1. Consoante dispõe o Artigo 550 do CPC: "Aquele que afirmar ser titular do direito de exigir contas requererá a citação do réu para que as preste ou conteste a ação no prazo de 15 (quinze) dias".
2. O Colendo Superior Tribunal de Justiça sedimentou a diretriz de que "o condômino tem legitimidade para exigir contas do síndico quando houver fundadas dúvidas quanto à higidez da gestão financeira, sendo inadmissível a recusa amparada em aprovação genérica de balancetes sintéticos".
3. A ausência de prestação mercantil configura quebra grave dos deveres fiduciários do gestor, ensejando a fixação de saldo devedor em segunda fase procedimental e potencial caracterização de Gestão Temerária e Apropriação Indébita (Art. 168 do CP).

IV - DOS PEDIDOS
Diante do exposto, requer a Vossa Excelência:
a) A CITAÇÃO do(a) Réu(é) para que, no prazo de 15 (quinze) dias, PRESTE AS CONTAS em forma mercantil/analítica, acompanhadas de todos os extratos bancários e notas fiscais do período, ou apresente contestação;
b) Julgada procedente a primeira fase, condenar o(a) Réu(é) a prestar as contas e, em segunda fase, apurar o saldo credor em favor da coletividade condominial;
c) A condenação do(a) Réu(é) nas custas processuais e honorários advocatícios sucumbenciais.

Dá-se à causa o valor preliminar de R$ {max(total_desvios, 10000.0):,.2f}.

Termos em que,
Pede Deferimento.

Comarca de {comarca}, {datetime.now().strftime('%d de %B de %Y')}.
"""
        OUTPUTS_NOTIFICACOES.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUTS_NOTIFICACOES / f"Minuta_Acao_Exigir_Contas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        out_file.write_text(minuta_judicial, encoding="utf-8")
        print(f"[Petição Criada] Salva em: {out_file}")

        return minuta_judicial

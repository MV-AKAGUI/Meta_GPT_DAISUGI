"""
Skill: Fundamentação Analítica do Direito à Informação & Notificação de Exibição
Utilizada pelo Subagente 3 (Especialista em Direito Condominial)
Fundamenta o direito individual do condômino com base no Art. 1.348, VIII e jurisprudência do STJ.
"""

from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.rag_engine import CondoRAGDatabase
from tools.sql_tool import CondoAuditDatabase
from config.drive_paths import OUTPUTS_NOTIFICACOES


class SkillFundamentacaoAnalitica:
    """Estrutura os fundamentos de direito material e processual para exibição de contas."""

    def __init__(self, rag_db: CondoRAGDatabase, sql_db: CondoAuditDatabase):
        self.rag = rag_db
        self.sql = sql_db

    def gerar_notificacao_exibicao(self, nome_condomino: str = "Condômino Notificante", unidade: str = "Unidade Autônoma") -> str:
        """
        Elabora a minuta completa de Notificação Extrajudicial para Exibição Integral
        de Extratos Bancários e Notas Fiscais com prazo peremptório.
        """
        # Consulta teses no RAG
        teses = self.rag.query_rag("legislacao_jurisprudencia", "prestação analítica extratos STJ obrigação síndico", n_results=2)
        teses_texto = "\n".join([f"• {t['texto'][:250]}..." for t in teses])

        # Consulta eventuais saídas órfãs já catalogadas
        saidas = self.sql.get_saidas_sem_comprovante()
        total_pendente = sum(abs(s["valor"]) for s in saidas)

        data_atual = datetime.now().strftime("%d de %B de %Y")

        minuta = f"""
================================================================================
NOTIFICAÇÃO EXTRAJUDICIAL COM PRAZO DETERMINADO
EXIBIÇÃO INTEGRAL DE DOCUMENTAÇÃO CONTÁBIL E EXTRATOS BANCÁRIOS
================================================================================

A(O) NOTIFICADO(A):
À Administração e Síndico(a) em Exercício do CONDOMÍNIO ONLY GUILLMON

NOTIFICANTE:
{nome_condomino}, proprietário(a) e condômino(a) da {unidade} do Condomínio Only Guillmon.

DO DIREITO À PRESTAÇÃO DE CONTAS ANALÍTICA E MERCANTIL:
Vem o(a) Notificante, no uso de suas prerrogativas legais asseguradas pelo Código Civil Brasileiro e pela jurisprudência pacífica do Superior Tribunal de Justiça (STJ), NOTIFICAR formalmente Vossa Senhoria para os fins de direito a seguir expostos:

1. DA OBRIGAÇÃO LEGAL DO SÍNDICO (ART. 1.348, VIII DO CÓDIGO CIVIL):
Dispõe expressamente o Artigo 1.348, inciso VIII do Código Civil que é dever indeclinável do síndico "prestar contas à assembleia, anualmente e quando exigidas".

2. DA JURISPRUDÊNCIA VINCULANTE DO STJ (FORMA ANALÍTICA COM EXTRATOS):
A prestação de contas condominial não se satisfaz com meros balancetes sintéticos ou demonstrativos genéricos. Conforme entendimento consagrado pelo Superior Tribunal de Justiça:
{teses_texto}

3. DO OBJETO DO REQUERIMENTO:
Requer-se, formalmente, a disponibilização integral, em meio digital e físico, no prazo IMPRORROGÁVEL de 10 (dez) dias úteis:
a) Cópia integral de todos os extratos bancários de todas as contas correntes, contas poupança e aplicações financeiras mantidas pelo condomínio no período auditado;
b) Cópia de todas as Notas Fiscais (NFS-e, DANFE), recibos e contratos que respaldam os débitos lançados, em especial o montante preliminar apurado de R$ {total_pendente:,.2f} cujos comprovantes não foram localizados no acervo comum;
c) Conciliação bancária integral demonstrando o vínculo entre cada saída financeira e sua causa legítima de interesse coletivo.

4. DAS ADVERTÊNCIAS LEGAIS:
O não atendimento à presente notificação dentro do prazo assinalado caracterizará a recusa injustificada de transparência, ensejando a propositura imediata da competente AÇÃO DE EXIGIR CONTAS (Art. 550 e seguintes do Código de Processo Civil), cumulada com pedido de fixação de honorários advocatícios e responsabilização pessoal por eventuais prejuízos causados à massa condominial (Art. 186 e 927 do CC).

São Paulo, {data_atual}.

_____________________________________________________________
{nome_condomino} - {unidade}
Condomínio Only Guillmon
================================================================================
"""
        # Salva o documento no diretório de outputs
        OUTPUTS_NOTIFICACOES.mkdir(parents=True, exist_ok=True)
        out_file = OUTPUTS_NOTIFICACOES / f"Notificacao_Exibicao_Documentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        out_file.write_text(minuta, encoding="utf-8")
        print(f"[Notificação Criada] Salva em: {out_file}")

        return minuta

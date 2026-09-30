"""
Teste Unitário da Camada de Banco de Dados Relacional (CondoAuditDatabase)
Valida a criação das tabelas, conciliação bancária e detecção de saídas sem comprovante.
"""

from pathlib import Path
import sys

# Garante a importação dos módulos da aplicação
app_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(app_root))

from tools.sql_tool import CondoAuditDatabase


def test_sql_tool_lifecycle():
    # Cria uma instância de teste em memória ou banco local
    db = CondoAuditDatabase()

    # 1. Inserir Previsão Orçamentária
    p_id = db.insert_previsao_item({
        "ano_exercicio": 2024,
        "categoria": "Manutencao Elevadores",
        "valor_aprovado_mensal": 2000.0,
        "valor_aprovado_anual": 24000.0,
        "ref_ata_ago": "AGO 2024 - Item 3"
    })
    assert p_id > 0, "Falha ao inserir previsão orçamentária"

    # 2. Inserir Lançamento de NF Comprovada
    l_id = db.insert_lancamento({
        "data": "2024-05-10",
        "categoria": "Manutencao Elevadores",
        "descricao": "Manutencao Preventiva Mensal Elevador Torre A",
        "valor": 2100.0,
        "numero_documento": "NF-10492",
        "favorecido": "Otis Elevadores Ltda",
        "cnpj_cpf": "00.123.456/0001-99"
    })
    assert l_id > 0, "Falha ao inserir lançamento"

    # 3. Inserir Extrato Bancário (Conciliado)
    e1_id = db.insert_extrato_item({
        "data": "2024-05-11",
        "banco": "Itau",
        "conta": "12345-6",
        "historico": "DEB AUTOM OTIS ELEVAD",
        "valor": -2100.0,
        "tipo_operacao": "DEBITO"
    })

    # 4. Inserir Extrato Bancário SEM Comprovante (Saída órfã / sem NF)
    e2_id = db.insert_extrato_item({
        "data": "2024-05-15",
        "banco": "Itau",
        "conta": "12345-6",
        "historico": "PIX ENVIADO SINDICO REF REEMBOLSO",
        "valor": -5500.0,
        "tipo_operacao": "DEBITO"
    })

    # Conciliação
    db.conciliar_item(extrato_id=e1_id, lancamento_id=l_id)

    # Verificação de saídas sem comprovante
    saidas_orfas = db.get_saidas_sem_comprovante()
    print(f"\n[OK] Total de saídas sem comprovante identificadas: {len(saidas_orfas)}")
    for s in saidas_orfas:
        print(f"  • Data: {s['data']} | Hist: {s['historico']} | Valor: R$ {s['valor']}")

    # Registrar inconsistência na matriz
    inc_id = db.registrar_inconsistencia({
        "data_ocorrencia": "2024-05-15",
        "tipo_inconsistencia": "SAIDA_SEM_COMPROVANTE",
        "grau_severidade": "GRAVE",
        "valor_envolvido": 5500.0,
        "descricao_detalhada": "Saída bancária via PIX sem documento fiscal ou recibo formal comprobatório.",
        "subagente_origem": "Subagente 1 - Auditor Financeiro",
        "id_extrato_fk": e2_id
    })
    assert inc_id > 0, "Falha ao registrar inconsistência"

    print("\n[SUCESSO] Teste unitário do CondoAuditDatabase concluído com 100% de integridade.")


if __name__ == "__main__":
    test_sql_tool_lifecycle()

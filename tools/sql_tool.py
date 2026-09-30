"""
Módulo de Banco de Dados Relacional (SQLite) para Auditoria Financeira
Projeto: Sistema de Auditoria e Prestação de Contas Condominial (MetaGPT)
Condomínio Only Guillmon
Arquivo de Banco: databases/condo_audit.db
"""

from pathlib import Path
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.drive_paths import SQLITE_DB_PATH, DATABASES_DIR


class CondoAuditDatabase:
    """Gerenciador do banco de dados relacional SQLite para auditoria financeira."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or SQLITE_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Cria e retorna uma conexão com row_factory configurado para acesso via dict."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Inicializa todas as tabelas e índices da memória relacional."""
        schema_sql = """
        -- Tabela de Lançamentos de Comprovantes e Notas Fiscais
        CREATE TABLE IF NOT EXISTS lancamentos_financeiros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,                          -- Data da NF/recibo (YYYY-MM-DD)
            categoria TEXT NOT NULL,                      -- Ex: Manutenção Elevadores, Limpeza, Água
            descricao TEXT NOT NULL,                      -- Descrição do serviço/produto
            valor REAL NOT NULL,                          -- Valor total comprovado
            tipo_operacao TEXT NOT NULL DEFAULT 'DEBITO', -- DEBITO ou CREDITO
            numero_documento TEXT,                        -- Número da NF, NFS-e, recibo
            favorecido TEXT,                              -- Nome / Razão Social do fornecedor
            cnpj_cpf TEXT,                                -- CNPJ ou CPF do favorecido
            status_conciliacao TEXT NOT NULL DEFAULT 'PENDENTE_COMPROVANTE',
            arquivo_origem TEXT,                          -- Nome do arquivo no Google Drive
            observacoes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabela de Extratos Bancários (Movimentação Financeira Efetiva)
        CREATE TABLE IF NOT EXISTS extratos_bancarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,                          -- Data da transação (YYYY-MM-DD)
            banco TEXT NOT NULL,                          -- Ex: Itaú, Bradesco, Santander
            conta TEXT,                                   -- Agência / Conta
            historico TEXT NOT NULL,                      -- Descrição literal constante no extrato
            documento_banco TEXT,                         -- Número do documento/autenticação no banco
            valor REAL NOT NULL,                          -- Valor (negativo para saídas, positivo para entradas)
            tipo_operacao TEXT NOT NULL,                  -- DEBITO ou CREDITO
            id_conciliacao_fk INTEGER REFERENCES lancamentos_financeiros(id) ON DELETE SET NULL,
            status_conciliacao TEXT NOT NULL DEFAULT 'NAO_CONCILIADO',
            arquivo_origem TEXT,                          -- Nome do extrato/OFX de origem
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabela de Previsão Orçamentária Aprovada em Assembleia
        CREATE TABLE IF NOT EXISTS previsao_orcamentaria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ano_exercicio INTEGER NOT NULL,               -- Ano de referência (Ex: 2024)
            categoria TEXT NOT NULL,                      -- Categoria de despesa orçada
            descricao TEXT,
            valor_aprovado_mensal REAL NOT NULL,          -- Valor teto mensal
            valor_aprovado_anual REAL NOT NULL,           -- Valor teto anual
            ref_ata_ago TEXT,                             -- Identificação da Ata que aprovou
            arquivo_origem TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Tabela de Inconsistências Apuradas (Alimenta a Matriz de Severidade)
        CREATE TABLE IF NOT EXISTS inconsistencias_auditoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_ocorrencia TEXT NOT NULL,                -- Data do fato
            tipo_inconsistencia TEXT NOT NULL,            -- SAIDA_SEM_COMPROVANTE, DESVIO_ORCAMENTARIO, DUPLICIDADE, NULIDADE
            grau_severidade TEXT NOT NULL,                -- GRAVE, MEDIO, LEVE
            valor_envolvido REAL DEFAULT 0.0,             -- Impacto financeiro
            descricao_detalhada TEXT NOT NULL,            -- Resumo circunstanciado da inconsistência
            subagente_origem TEXT NOT NULL,               -- Subagente que identificou o achado
            id_extrato_fk INTEGER REFERENCES extratos_bancarios(id) ON DELETE SET NULL,
            id_lancamento_fk INTEGER REFERENCES lancamentos_financeiros(id) ON DELETE SET NULL,
            resolvido INTEGER NOT NULL DEFAULT 0,         -- 0 para pendente, 1 para sanado/justificado
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Índices para alta performance em conciliação
        CREATE INDEX IF NOT EXISTS idx_lanc_data_valor ON lancamentos_financeiros(data, valor);
        CREATE INDEX IF NOT EXISTS idx_lanc_status ON lancamentos_financeiros(status_conciliacao);
        CREATE INDEX IF NOT EXISTS idx_extrato_data_valor ON extratos_bancarios(data, valor);
        CREATE INDEX IF NOT EXISTS idx_extrato_status ON extratos_bancarios(status_conciliacao);
        CREATE INDEX IF NOT EXISTS idx_prev_ano_cat ON previsao_orcamentaria(ano_exercicio, categoria);
        """

        with self.get_connection() as conn:
            conn.executescript(schema_sql)

    # ================= MÉTODOS DE INSERÇÃO =================

    def insert_lancamento(self, dados: Dict[str, Any]) -> int:
        """Insere um lançamento comprovado (NF / recibo) e retorna o ID."""
        sql = """
        INSERT INTO lancamentos_financeiros (
            data, categoria, descricao, valor, tipo_operacao,
            numero_documento, favorecido, cnpj_cpf,
            status_conciliacao, arquivo_origem, observacoes
        ) VALUES (
            :data, :categoria, :descricao, :valor, :tipo_operacao,
            :numero_documento, :favorecido, :cnpj_cpf,
            :status_conciliacao, :arquivo_origem, :observacoes
        )
        """
        defaults = {
            "tipo_operacao": "DEBITO",
            "numero_documento": None,
            "favorecido": None,
            "cnpj_cpf": None,
            "status_conciliacao": "PENDENTE_COMPROVANTE",
            "arquivo_origem": None,
            "observacoes": None
        }
        params = {**defaults, **dados}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid

    def insert_extrato_item(self, dados: Dict[str, Any]) -> int:
        """Insere uma linha de extrato bancário e retorna o ID."""
        sql = """
        INSERT INTO extratos_bancarios (
            data, banco, conta, historico, documento_banco,
            valor, tipo_operacao, id_conciliacao_fk,
            status_conciliacao, arquivo_origem
        ) VALUES (
            :data, :banco, :conta, :historico, :documento_banco,
            :valor, :tipo_operacao, :id_conciliacao_fk,
            :status_conciliacao, :arquivo_origem
        )
        """
        defaults = {
            "conta": None,
            "documento_banco": None,
            "id_conciliacao_fk": None,
            "status_conciliacao": "NAO_CONCILIADO",
            "arquivo_origem": None
        }
        params = {**defaults, **dados}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid

    def insert_previsao_item(self, dados: Dict[str, Any]) -> int:
        """Insere um item de previsão orçamentária anual."""
        sql = """
        INSERT INTO previsao_orcamentaria (
            ano_exercicio, categoria, descricao,
            valor_aprovado_mensal, valor_aprovado_anual,
            ref_ata_ago, arquivo_origem
        ) VALUES (
            :ano_exercicio, :categoria, :descricao,
            :valor_aprovado_mensal, :valor_aprovado_anual,
            :ref_ata_ago, :arquivo_origem
        )
        """
        defaults = {"descricao": None, "ref_ata_ago": None, "arquivo_origem": None}
        params = {**defaults, **dados}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid

    # ================= MÉTODOS ANALÍTICOS DE CONCILIAÇÃO =================

    def conciliar_item(self, extrato_id: int, lancamento_id: int) -> bool:
        """Vincula um item de extrato com seu respectivo lançamento comprovado."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE extratos_bancarios
                SET id_conciliacao_fk = ?, status_conciliacao = 'CONCILIADO'
                WHERE id = ?
            """, (lancamento_id, extrato_id))

            cursor.execute("""
                UPDATE lancamentos_financeiros
                SET status_conciliacao = 'CONCILIADO'
                WHERE id = ?
            """, (lancamento_id,))
            conn.commit()
            return True

    def get_saidas_sem_comprovante(self) -> List[Dict[str, Any]]:
        """Retorna todos os débitos bancários que não possuem nota fiscal / comprovante vinculado."""
        sql = """
        SELECT id, data, banco, historico, valor, arquivo_origem
        FROM extratos_bancarios
        WHERE tipo_operacao = 'DEBITO' AND status_conciliacao = 'NAO_CONCILIADO'
        ORDER BY data ASC, ABS(valor) DESC
        """
        with self.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [dict(r) for r in rows]

    def get_desvios_orcamentarios(self, ano_exercicio: int) -> List[Dict[str, Any]]:
        """
        Calcula o total realizado por categoria contra o teto anual aprovado na AGO.
        """
        sql = """
        SELECT 
            p.categoria,
            p.valor_aprovado_anual AS teto_orcado,
            COALESCE(SUM(l.valor), 0.0) AS total_realizado,
            ROUND(COALESCE(SUM(l.valor), 0.0) - p.valor_aprovado_anual, 2) AS desvio_absoluto,
            ROUND(((COALESCE(SUM(l.valor), 0.0) - p.valor_aprovado_anual) / p.valor_aprovado_anual) * 100.0, 2) AS percentual_desvio
        FROM previsao_orcamentaria p
        LEFT JOIN lancamentos_financeiros l 
            ON p.categoria = l.categoria 
            AND strftime('%Y', l.data) = CAST(p.ano_exercicio AS TEXT)
            AND l.tipo_operacao = 'DEBITO'
        WHERE p.ano_exercicio = ?
        GROUP BY p.categoria
        HAVING total_realizado > p.valor_aprovado_anual
        ORDER BY desvio_absoluto DESC
        """
        with self.get_connection() as conn:
            rows = conn.execute(sql, (ano_exercicio,)).fetchall()
            return [dict(r) for r in rows]

    def registrar_inconsistencia(self, dados: Dict[str, Any]) -> int:
        """Registra um achado grave/médio na matriz de inconsistências."""
        sql = """
        INSERT INTO inconsistencias_auditoria (
            data_ocorrencia, tipo_inconsistencia, grau_severidade,
            valor_envolvido, descricao_detalhada, subagente_origem,
            id_extrato_fk, id_lancamento_fk
        ) VALUES (
            :data_ocorrencia, :tipo_inconsistencia, :grau_severidade,
            :valor_envolvido, :descricao_detalhada, :subagente_origem,
            :id_extrato_fk, :id_lancamento_fk
        )
        """
        defaults = {"valor_envolvido": 0.0, "id_extrato_fk": None, "id_lancamento_fk": None}
        params = {**defaults, **dados}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor.lastrowid

    def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Executa consultas arbitrárias com proteção."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def to_dataframe(self, table_name: str) -> pd.DataFrame:
        """Converte uma tabela completa em DataFrame para análise do Subagente 1."""
        with self.get_connection() as conn:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)


if __name__ == "__main__":
    db = CondoAuditDatabase()
    print("Banco de dados SQLite inicializado com sucesso!")
    print(f"Caminho do arquivo: {db.db_path}")

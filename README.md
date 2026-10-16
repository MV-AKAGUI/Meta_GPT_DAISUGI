# Meta_GPT_DAISUGI v2.0

**Especialista em Geração Automática de SDD, C4 Diagrams e Artefatos de Engenharia**

---

## 🎯 Propósito

Meta_GPT_DAISUGI é uma customização do **Meta_GPT** para o ecossistema DAISUGI. Gera automaticamente:

- **SDD** (Especificação de Sistema Detalhada)
- **C4 Diagrams** (Contexto, Container, Component)
- **Prisma Schemas** (Models de banco de dados)
- **Pydantic Contracts** (Validação de API)
- **Testes de Exemplo** (Sample test suites)

**Ideal para:** SUGOI_CADEIA_DE_VALOR, Designer de Processos (BPM/HAP/EAP), Arquitetura de Sistemas Corporativos.

---

## 📋 Requisitos

- **Python 3.9+**
- **pip install metagpt** (Meta_GPT oficial)
- **Briefing em Markdown** (FASE_1_OTIMIZADA.md ou similar)

---

## 🚀 Uso Rápido

```bash
# Ativar ambiente
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Instalar Meta_GPT
pip install metagpt --upgrade

# Executar geração
metagpt --project <NOME_PROJETO> \
  --spec <CAMINHO_BRIEFING.md> \
  --output <DIRETÓRIO_SAÍDA>/
```

**Exemplo para SUGOI:**

```bash
metagpt --project SUGOI_Cadeia_Valor_FASE1 \
  --spec ./../FERRAMENTAS--FUZZY---HARNESS-/.claude/FASE_1_OTIMIZADA.md \
  --output ./output/fase1_autogen/
```

---

## 📂 Estrutura

```
Meta_GPT_DAISUGI/
├── .venv/                   # Ambiente virtual Python
├── metagpt/                 # Customizações e templates
├── config/                  # Configurações (chaves API, paths)
├── tools/                   # Ferramentas auxiliares
├── skills/                  # Skills customizadas
├── subagents/               # Sub-agentes especializados
├── outputs/                 # Artefatos gerados (SDD, C4, Schemas)
├── tests/                   # Testes de validação
├── docs/                    # Documentação
├── README.md                # Este arquivo
└── requirements.txt         # Dependências (gerado por Meta_GPT)
```

---

## 🔧 Customizações DAISUGI

### Modelos Ollama Integrados (Cascata)

```
DeepSeek-R1 8B  → Análise BPM/HAP estrutural (95% confiança)
Qwen2.5-Coder   → Geração de código/schemas (85% confiança)
SaulLM 7B       → Análise de compliance jurídico (98% confiança)
```

### Generators Personalizados

- `SDD_Generator`: Gera especificações completas a partir de briefing
- `C4_Generator`: Mermaid diagrams automáticos
- `Prisma_Generator`: Schemas ORM prontos para execução
- `Pydantic_Generator`: Validação de contratos de API

---

## 📊 Outputs Esperados

Depois de executar Meta_GPT, você terá em `output/<PROJECT>/`:

```
├── SDD_AUTOGEN.md                 # Especificação de 500+ linhas
├── C4_DIAGRAMS.md                 # Mermaid diagrams (Context, Container, Component)
├── Architecture_Overview.md        # Resumo da arquitetura
├── prisma/
│   └── schema.prisma              # Modelos de banco de dados auto-gerados
├── src/
│   └── schemas.pydantic.py        # Validadores de API
├── tests/
│   └── sample.test.ts             # Testes de exemplo (TypeScript)
├── API_Contracts.md               # Documentação de endpoints
└── RACI_Matrix.md                 # Matriz de responsabilidades
```

---

## 🔐 Segurança & Compliance

- ✅ **Guardrails Anti-Alucinação**: 3 camadas de validação
- ✅ **Fuzzy Confidence Scoring**: Toda sugestão tem % de confiança
- ✅ **Auditoria Imutável**: Logs em DB (append-only)
- ✅ **LGPD Ready**: Sem PII em outputs por padrão
- ✅ **SoD Determinístico**: Separação de deveres (20 regras, 100% confidence)

---

## 🤖 Integração com Dai_Vibe_Code

Meta_GPT_DAISUGI é acionado por **Dai_Vibe_Code** durante:

1. **TEMPO 1**: Escuta Ativa → Coleta briefing
2. **TEMPO 2**: Grill-Me → Valida premissas
3. **TEMPO 3**: Anatomia Técnica
   - ✅ Meta_GPT_DAISUGI gera SDD + C4
   - ✅ Validação automática (14 setores? RACI? Swagger?)
   - ✅ Gate: "De Acordo com a arquitetura?"

---

## 📌 Próximas Integrações

- [ ] n8n Workflow: Orquestração de SDD → Prisma → Testes
- [ ] Dify: Interface low-code para customizações
- [ ] LangChain Graph: Dependency mapping automático
- [ ] RAG + pgvector: Busca semântica em histórico de SDDs

---

## 🆘 Troubleshooting

**Meta_GPT não encontrado?**
```bash
pip install metagpt --upgrade
metagpt --version
```

**Erro ao gerar Prisma schema?**
- Verificar: Briefing tem 14 setores definidos?
- Verificar: RACI matrix está presente no briefing?
- Fallback: Gerar schema manualmente (prisma init)

**Outputs vazios?**
- Verificar: OpenAI API key está configurada? (ou Ollama rodando?)
- Verificar: Arquivo de briefing existe e tem > 200 linhas?

---

## 📝 Licença & Atribuição

Meta_GPT_DAISUGI é uma customização de **Meta_GPT** (open-source).

- Base: https://github.com/geekan/MetaGPT
- DAISUGI Customizations: https://github.com/MV-AKAGUI/Meta_GPT_DAISUGI
- Maintained by: Ronaldo Akagui (MV-AKAGUI)

---

**Versão:** 2.0 SUGOI-Ready  
**Status:** Production  
**Última atualização:** 2026-10-16  
**Repositório:** https://github.com/MV-AKAGUI/Meta_GPT_DAISUGI

# API RAG Educacional

API de Assistente Educacional que cria rotas de aprendizagem personalizadas baseadas em métricas de estudantes e recuperação aumentada (RAG).

## 🎯 Objetivo

Fornecer recomendações pedagógicas personalizadas analisando o perfil do estudante através de 14 métricas em 2 camadas:
- **Camada A**: Diagnóstico geral (risco, prontidão)
- **Camada B**: Diagnóstico específico (base matemática, autonomia, dificuldades)

## 🏗️ Arquitetura

- **FastAPI** - API REST
- **LangChain** - Orquestração de LLM
- **Groq** - Modelo de linguagem
- **Qdrant** - Banco vetorial para RAG
- **MySQL** - Dados educacionais (disciplinas, vídeos, literatura)
- **Docker** - Containerização

## 📋 Endpoints

### `GET /healthz`
Verifica se a API está operacional.

**Response:** `200 OK`
```json
{"status": "ok"}
```

---

### `POST /ask`
Gera recomendação de rota de aprendizagem para um estudante.

**Request:**
```json
{
  "question": "Como devo estudar cálculo?",
  "context": null
}
```

**Response:** `200 OK`
```json
{
  "answer": "📊 DIAGNÓSTICO:\n- Risco identificado: medio (score: 60/100)\n- Dificuldade principal: calculo\n- Prontidão: 30/100\n- Autonomia: baixa\n\n🎯 ROTA PERSONALIZADA:\n..."
}
```

**Status Codes:**
- `200` - Sucesso
- `400` - Erro genérico
- `422` - Validação falhou
- `500` - Erro do servidor

---

### `POST /ingest`
Copia o banco de dados MySQL para backup e carrega documentos no Qdrant.

**Request:**
```json
{}
```

**Response:** `200 OK`
```json
{
  "ingested": true,
  "status": "success",
  "message": "Banco de dados copiado com sucesso",
  "backup_file": "backups/db_mmp_backup_20260420_143022.sql",
  "timestamp": "20260420_143022"
}
```

**Status Codes:**
- `200` - Sucesso
- `400` - Erro (dados inválidos)
- `404` - Nenhum documento encontrado
- `503` - Banco de dados indisponível

---

## 📊 Métricas do Estudante

Todas as métricas devem ser enviadas via `POST /ask` no corpo da requisição (será implementado no frontend).

### Camada A - Diagnóstico Geral

| Campo | Tipo | Valores | Descrição |
|-------|------|---------|-----------|
| `perfil_risco` | categórico | baixo, medio, alto | Nível geral de risco acadêmico |
| `score_risco` | numérico | 0-100 | Score contínuo de risco |
| `necessidade_de_intervencao` | categórico | baixa, media, alta | Urgência de ação pedagógica |
| `score_prontidao_geral` | numérico | 0-100 | Prontidão acadêmica geral |

### Camada B - Diagnóstico Específico

| Campo | Tipo | Valores | Descrição |
|-------|------|---------|-----------|
| `nivel_base_matematica` | categórico | insuficiente, basico, intermediario, adequado | Nível de base matemática |
| `score_base_matematica` | numérico | 0-100 | Score da base matemática |
| `autonomia_do_aluno` | categórico | baixa, media, alta | Capacidade de estudar independentemente |
| `score_autonomia` | numérico | 0-100 | Score contínuo de autonomia |
| `necessidade_de_suporte` | categórico | baixa, media, alta | Intensidade de apoio necessário |
| `dificuldade_predominante` | categórico | calculo, algebra, geometria, interpretacao, logica | Principal fragilidade pedagógica |
| `ponto_de_partida_recomendado` | categórico | basico, intermediario, avancado | Nível inicial da trilha |
| `prontidao_para_avancar` | categórico | nao_pronto, quase_pronto, pronto | Desbloqueio de progressão |
| `score_prontidao_calculo` | numérico | 0-100 | Prontidão específica para cálculo |
| `intensidade_de_recomendacao` | categórico | leve, moderada, intensiva | Volume/profundidade das recomendações |

### Exemplo de JSON de Métricas

```json
{
  "id_aluno": 1,
  "perfil_risco": "medio",
  "score_risco": 60,
  "necessidade_de_intervencao": "media",
  "score_prontidao_geral": 30,
  "nivel_base_matematica": "insuficiente",
  "score_base_matematica": 27,
  "autonomia_do_aluno": "baixa",
  "score_autonomia": 17,
  "necessidade_de_suporte": "alta",
  "dificuldade_predominante": "calculo",
  "ponto_de_partida_recomendado": "basico",
  "prontidao_para_avancar": "nao_pronto",
  "score_prontidao_calculo": 25,
  "intensidade_de_recomendacao": "intensiva"
}
```

---

## 🚀 Como Usar

### 1. Subir com Docker dependências dos projetos ia_mmp e app_mmp

```bash
docker compose up --build
```

### 2. Conectar redes de ambos os projetos
```bash
docker network connect app_mmp_default ia-api
```

### 3. Verificar saúde da API

```bash
curl http://localhost:8000/healthz
```

### 4. Ingerir dados do banco

```bash
curl.exe -X POST http://localhost:8000/ingest
```

### 5. Fazer pergunta com métricas do estudante

```bash
curl.exe -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Como devo estudar cálculo?\", \"context\": null}"
```

**Com métricas (quando implementado):**
```bash
curl.exe -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"Rota voltada a calculo\", \"student_metrics\": {\"id_aluno\": 1, \"perfil_risco\": \"medio\", \"score_risco\": 60, \"necessidade_de_intervencao\": \"media\", \"score_prontidao_geral\": 30, \"nivel_base_matematica\": \"insuficiente\", \"score_base_matematica\": 27, \"autonomia_do_aluno\": \"baixa\", \"score_autonomia\": 17, \"necessidade_de_suporte\": \"alta\", \"dificuldade_predominante\": \"calculo\", \"ponto_de_partida_recomendado\": \"basico\", \"prontidao_para_avancar\": \"nao_pronto\", \"score_prontidao_calculo\": 25, \"intensidade_de_recomendacao\": \"intensiva\"}}"
```

---

## ⚙️ Configuração

Variáveis de ambiente (`.env`):

```env
# ==========================================
# LLM - GROQ
# ==========================================
# Obtenha em: https://grok.ai/settings/tokens
GROQ_API_KEY=sua_chave_aqui

# Modelo LLM
LLM_MODEL=llama-3.3-70b-versatile


# ==========================================
# MYSQL - BANCO RELACIONAL
# ==========================================
# Use localhost se rodar fora do Docker
# Use db_mmp se rodar via Docker Compose
DB_HOST=db_mmp

DB_PORT=3306
DB_USER=app_mmp
DB_PASS=app_mmp
DB_NAME=db_mmp


# ==========================================
# QDRANT - VECTOR DATABASE
# ==========================================
QDRANT_HOST=qdrant
QDRANT_PORT=6333

# Mantive "documents" (era o padrão original)
QDRANT_COLLECTION=documents


# ==========================================
# EMBEDDINGS
# ==========================================
EMBEDDINGS_MODEL=sentence-transformers/all-mpnet-base-v2


# ==========================================
# CHUNKING
# ==========================================
CHUNK_SIZE=1000

# Mantive 150 (melhor para contexto)
CHUNK_OVERLAP=150


# ==========================================
# RETRIEVAL
# ==========================================
RETRIEVER_K=4


# ==========================================
# API
# ==========================================
API_HOST=0.0.0.0
API_PORT=8000


# ==========================================
# DEBUG
# ==========================================
DEBUG=False
LOG_LEVEL=INFO
```

---

## 🧪 Testes

```bash
# Executar testes
pytest teste.py -v

# Com cobertura
pytest teste.py --cov=main --cov=models --cov=chain --cov=ingest

# Menu interativo
python run_tests.py
```

---

## 📁 Estrutura do Projeto

```
api/
├── main.py              # Endpoints FastAPI
├── chain.py             # Orquestração LLM
├── config.py            # Configurações e SYSTEM_PROMPT
├── models.py            # Modelos Pydantic
├── retriever.py         # Busca vetorial
├── vectorstore.py       # Gerenciador Qdrant
├── db_loader.py         # Carregamento MySQL
├── ingest.py            # Pipeline de ingestão
├── teste.py             # Testes unitários
├── conftest.py          # Fixtures pytest
├── pytest.ini           # Configuração pytest
├── run_tests.py         # Script de testes com menu
└── Dados/               # Dados CSV
```

---

## 🔄 Fluxo de Funcionamento

1. **Ingestão** (`/ingest`):
   - Conecta ao MySQL
   - Carrega tabelas: videos, literature, disciplines
   - Cria embeddings
   - Armazena no Qdrant
   - Faz backup do banco

2. **Pergunta** (`/ask`):
   - Recebe pergunta + métricas do estudante
   - Busca documentos relevantes no Qdrant (RAG)
   - Enriquece contexto com recursos educacionais
   - Passa para LLM Groq com SYSTEM_PROMPT
   - Retorna rota de aprendizagem personalizada

---

## 📚 Recursos Educacionais

### Tabelas MySQL
- **disciplines**: Disciplinas com ementa, pré-requisitos, carga horária
- **videos**: Conteúdo em vídeo com plataforma, duração, nível
- **literature**: Literatura acadêmica com tipo, autores, instituição

---

## ⚠️ Tratamento de Erros

| Erro | Código | Causa |
|------|--------|-------|
| Falha conexão MySQL | `503` | Banco indisponível |
| Nenhum documento | `404` | Banco vazio |
| JSON inválido | `422` | Validação Pydantic falhou |
| Erro genérico | `400` | Outro erro |

---

## 🛠️ Stack Técnico

- Python 3.11+
- FastAPI 0.135+
- LangChain 0.3+
- Groq API
- Qdrant
- MySQL
- Docker & Docker Compose

---

## 📖 Documentação Adicional

- [TESTING.md](TESTING.md) - Guia completo de testes
- [QUICKSTART.md](QUICKSTART.md) - Início rápido

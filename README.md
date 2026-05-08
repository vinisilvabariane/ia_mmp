# API Educacional com Rotas Estruturadas

API em FastAPI para gerar rotas educacionais personalizadas. A aplicacao continua usando LLM para gerar consultas SQL seguras, mas agora separa claramente:

- recuperacao de contexto via SQL;
- inferencia pedagogica auditavel em Python;
- resposta estruturada com schema Pydantic;
- renderizacao textual opcional da rota.

## Arquitetura atual

- FastAPI para exposicao da API
- LangChain + Groq para geracao das queries SQL
- MySQL como fonte de recursos educacionais
- `LearningRoute` como objeto central da resposta
- Heuristicas em Python para diagnostico, ritmo e montagem da trilha

## Fluxo

1. O cliente envia pergunta e metricas para `POST /routes/generate`.
2. A LLM gera ate uma query por categoria:
   - `videos_query`
   - `literature_query`
   - `disciplines_query`
3. O repositorio valida e executa apenas `SELECT` com tabelas permitidas.
4. O `LearningRouteBuilder` transforma metrica + recursos em uma rota tipada.
5. O cliente pode:
   - consumir o JSON estruturado;
   - chamar `POST /routes/explain` para obter a versao textual;
   - continuar usando `POST /ask` como endpoint legado.

## Endpoints

### `GET /healthz`

Status basico da API.

### `GET /healthz/live`

Liveness check.

### `GET /healthz/ready`

Readiness check com verificacao de configuracao e banco.

### `POST /routes/generate`

Gera a rota estruturada.

Exemplo:

```json
{
    "question": "Quero aprender cálculo do zero",
    "student_metrics": {
      "risk_score": 72,
      "general_readiness_score": 41,
      "mathematical_foundation_score": 33,
      "autonomy_score": 28
    },
    "educational_form_responses": [
      {
        "question": "Quais conteúdos você mais domina?",
        "answer": "Tenho dificuldade em álgebra e funções."
      },
      {
        "question": "Como prefere estudar?",
        "answer": "Videoaulas e exercícios práticos."
      }
    ]
  }
```

Resposta resumida:

```json
{
  "route": {
    "question": "Como devo estudar calculo?",
    "diagnosis": {
      "risk_score": 72,
      "general_readiness_score": 41,
      "mathematical_foundation_score": 33,
      "autonomy_score": 28,
      "support_level": "alta",
      "starting_level": "fundamentos e prerequisitos",
      "pace": "passos curtos com checkpoints frequentes",
      "confidence_note": "As decisoes foram inferidas diretamente das metricas recebidas.",
      "summary": "..."
    },
    "stages": [],
    "checkpoints": [],
    "alternative_plan": {},
    "prioritized_resources": {},
    "generated_queries": {
      "videos_query": "SELECT ...",
      "literature_query": "SELECT ...",
      "disciplines_query": "SELECT ..."
    }
  }
}
```

### `POST /routes/explain`

Recebe um objeto `LearningRoute` e devolve a versao textual.

### `POST /ask`

Endpoint legado. Internamente ele gera a rota e devolve o texto renderizado.

## Estrutura esperada no banco

- `videos`
- `literature`
- `disciplines`

Os arquivos em [`data`](/C:/Users/Usuario/Documents/ia_mmp/data) ja estao em UTF-8. A aplicacao trata normalizacao textual no fluxo de recomendacao.

## Variaveis de ambiente

Use [`.env.example`](/C:/Users/Usuario/Documents/ia_mmp/.env.example) como base.

```env
GROQ_API_KEY=your_groq_api_key_here
DB_HOST=db_mmp
DB_PORT=3306
DB_USER=app_mmp
DB_PASS=app_mmp
DB_NAME=db_mmp
LLM_MODEL=llama-3.3-70b-versatile
LLM_TIMEOUT_SECONDS=15
LLM_MAX_RETRIES=1
SQL_SEARCH_LIMIT=9
DB_CONNECT_TIMEOUT_SECONDS=5
DEBUG=False
LOG_LEVEL=INFO
```

## Testes

Os testes cobrem:

- validacao dos payloads;
- sanitizacao SQL;
- heuristica de montagem de rota;
- renderizacao textual;
- tratamento de erro HTTP.

Execucao:

```bash
pytest
```

## Execucao com Docker

```bash
docker compose up --build
```

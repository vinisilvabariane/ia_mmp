from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chain import ask
from ingest import run_ingest

from models import AskPayload

app = FastAPI(
    title="IA API",
    description="API RAG enxuta com ingest e consulta via LLM",
    version="2.0.0",
)

@app.get("/healthz")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/ask")
def rag_ask(payload: AskPayload) -> dict[str, Any]:
    try:
        return {"answer": ask(payload.question, payload.student_metrics or {})}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
def rag_ingest() -> dict[str, Any]:
    try:
        result = run_ingest()
        return {"ingested": True, **result}
    except ConnectionError as exc:
        # Erro de conexão com banco de dados -> 503 Service Unavailable
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        # Nenhum documento encontrado -> 404 Not Found
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        # Outros erros -> 400 Bad Request
        raise HTTPException(status_code=400, detail=str(exc)) from exc

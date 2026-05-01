import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.core.logging import setup_logging
from app.routes import api_router

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="IA API",
    description="API de recomendacao educacional com consulta SQL via LLM e geracao estruturada de rotas",
    version="3.0.0",
)

app.include_router(api_router)


@app.exception_handler(AppError)
def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "detail": exc.message},
    )


@app.exception_handler(Exception)
def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected_error", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "Erro interno nao tratado."},
    )

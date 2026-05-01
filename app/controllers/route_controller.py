from typing import Any

from fastapi import APIRouter

from app.schemas.ask import AskPayload
from app.schemas.route import ExplainRouteRequest, ExplainRouteResponse, GenerateRouteRequest, GenerateRouteResponse
from app.services.rag_service import RagService

router = APIRouter()
service = RagService()


@router.post("/ask")
def ask(payload: AskPayload) -> dict[str, Any]:
    answer = service.ask(
        question=payload.question,
        student_metrics=payload.student_metrics,
    )
    return {"answer": answer}


@router.post("/generate", response_model=GenerateRouteResponse)
def generate_route(payload: GenerateRouteRequest) -> GenerateRouteResponse:
    route = service.generate_route(
        question=payload.question,
        student_metrics=payload.student_metrics,
    )
    return GenerateRouteResponse(route=route)


@router.post("/explain", response_model=ExplainRouteResponse)
def explain_route(payload: ExplainRouteRequest) -> ExplainRouteResponse:
    return ExplainRouteResponse(explanation=service.explain_route(payload.route))

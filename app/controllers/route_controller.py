from typing import Any

from app.services.metrics_service import MetricsService
from fastapi import APIRouter

from app.schemas.route import ExplainRouteRequest, ExplainRouteResponse, GenerateMetricsRequest, GenerateRouteRequest, GenerateRouteResponse, StudentMetrics
from app.services.rag_service import RagService

router = APIRouter()
service = RagService()
metrics_service = MetricsService()


@router.post("/ask")
def ask(payload: GenerateRouteRequest) -> dict[str, Any]:
    answer = service.ask(
        question=payload.question,
        student_metrics=payload.student_metrics,
        educational_form_responses=payload.educational_form_responses,
    )
    return {"answer": answer}


@router.post("/generate", response_model=GenerateRouteResponse)
def generate_route(payload: GenerateRouteRequest) -> GenerateRouteResponse:
    route = service.generate_route(
        question=payload.question,
        student_metrics=payload.student_metrics,
        educational_form_responses=payload.educational_form_responses,
    )
    return GenerateRouteResponse(route=route)

@router.post("/generate-metrics", response_model=StudentMetrics)
def generate_metrics(payload: GenerateMetricsRequest) -> StudentMetrics:
    metrics = metrics_service.generate_metrics(
        educational_form_responses=payload.educational_form_responses,
    )
    return metrics

@router.post("/explain", response_model=ExplainRouteResponse)
def explain_route(payload: ExplainRouteRequest) -> ExplainRouteResponse:
    return ExplainRouteResponse(explanation=service.explain_route(payload.route))

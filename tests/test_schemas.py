import pytest
from pydantic import ValidationError

from app.schemas.route import GenerateRouteRequest


def test_generate_route_request_validates_metric_ranges() -> None:
    with pytest.raises(ValidationError):
        GenerateRouteRequest(
            question="Como estudar calculo?",
            student_metrics={"risk_score": 120},
        )


def test_generate_route_request_requires_non_empty_question() -> None:
    with pytest.raises(ValidationError):
        GenerateRouteRequest(question="", student_metrics={})


def test_generate_route_request_accepts_question_answer_context() -> None:
    payload = GenerateRouteRequest(
        question="Como estudar calculo?",
        educational_form_responses=[
            {"question": "O que devo revisar antes?", "answer": "Tenho dificuldade em funcoes e algebra."}
        ],
    )

    assert len(payload.educational_form_responses) == 1
    assert payload.educational_form_responses[0].question == "O que devo revisar antes?"


def test_generate_route_request_rejects_empty_question_answer_context_fields() -> None:
    with pytest.raises(ValidationError):
        GenerateRouteRequest(
            question="Como estudar calculo?",
            educational_form_responses=[{"question": "", "answer": "Resposta valida"}],
        )

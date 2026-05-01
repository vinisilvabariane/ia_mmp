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

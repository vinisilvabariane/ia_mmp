from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.errors import DependencyAppError
from app.main import app


def test_generate_route_returns_typed_error_payload() -> None:
    client = TestClient(app)

    with patch(
        "app.controllers.route_controller.service.generate_route",
        side_effect=DependencyAppError("Banco indisponivel."),
    ):
        response = client.post(
            "/routes/generate",
            json={"question": "Como estudar calculo?", "student_metrics": {"risk_score": 50}},
        )

    assert response.status_code == 503
    assert response.json() == {
        "error": "dependency_unavailable",
        "detail": "Banco indisponivel.",
    }


def test_generate_metrics_returns_typed_metrics_payload() -> None:
    client = TestClient(app)

    response = client.post(
        "/routes/generate-metrics",
        json={
            "educational_form_responses": [
                {
                    "question": "Quais sao suas dificuldades?",
                    "answer": "Tenho dificuldade em algebra e procrastino bastante.",
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {
        "risk_score",
        "general_readiness_score",
        "mathematical_foundation_score",
        "autonomy_score",
    }
    assert payload["risk_score"] >= 0
    assert payload["mathematical_foundation_score"] <= 100

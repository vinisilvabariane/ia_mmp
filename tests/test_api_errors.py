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

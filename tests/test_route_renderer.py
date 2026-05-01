from app.schemas.route import ResourceQuerySet, StudentMetrics
from app.services.route_builder import LearningRouteBuilder
from app.services.route_renderer import RouteRenderer


def test_route_renderer_contains_expected_sections() -> None:
    builder = LearningRouteBuilder()
    renderer = RouteRenderer()
    route = builder.build(
        question="Como estudar algebra linear?",
        metrics=StudentMetrics(
            risk_score=20,
            general_readiness_score=80,
            mathematical_foundation_score=85,
            autonomy_score=78,
        ),
        queries=ResourceQuerySet(),
        resources={"disciplines_query": [], "videos_query": [], "literature_query": []},
    )

    explanation = renderer.render(route)

    assert "DIAGNOSTICO DO MOMENTO" in explanation
    assert "ROTA DE APRENDIZAGEM DINAMICA" in explanation
    assert "PLANO ALTERNATIVO" in explanation

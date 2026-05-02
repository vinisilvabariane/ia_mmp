from app.schemas.route import QuestionAnswerContext
from app.services.metrics_service import MetricsService


def test_generate_metrics_infers_low_autonomy_and_high_risk_from_negative_context() -> None:
    service = MetricsService()

    metrics = service.generate_metrics(
        educational_form_responses=[
            QuestionAnswerContext(
                question="Quais sao suas maiores dificuldades?",
                answer="Estou perdido, procrastino muito e tenho dificuldade em algebra e funcoes.",
            )
        ],
    )

    assert metrics.risk_score is not None and metrics.risk_score >= 65
    assert metrics.mathematical_foundation_score is not None and metrics.mathematical_foundation_score <= 40
    assert metrics.autonomy_score is not None and metrics.autonomy_score <= 40


def test_generate_metrics_blends_existing_metrics_with_inferred_context() -> None:
    service = MetricsService()

    metrics = service.generate_metrics(
        educational_form_responses=[
            QuestionAnswerContext(
                question="Como voce estuda?",
                answer="Tenho rotina, estudo sozinho, mas estou um pouco travado com a base.",
            )
        ],
    )

    assert metrics.risk_score is not None and metrics.risk_score < 60
    assert metrics.autonomy_score is not None and metrics.autonomy_score >= 60


def test_generate_metrics_returns_neutral_scores_when_called_without_context() -> None:
    service = MetricsService()

    metrics = service.generate_metrics()

    assert metrics.model_dump() == {
        "risk_score": 50,
        "general_readiness_score": 50,
        "mathematical_foundation_score": 50,
        "autonomy_score": 50,
    }

from app.schemas.route import QuestionAnswerContext
from app.services.metrics_service import MetricsService


class FakeMetricsRepository:
    def fetch_active_metric_keys(self) -> list[str]:
        return [
            "risk_score",
            "general_readiness_score",
            "mathematical_foundation_score",
            "autonomy_score",
        ]

    def fetch_question_metric_rules(self, *, question_keys: list[str] | None = None, question_texts: list[str] | None = None) -> list[dict]:
        return [
            {
                "question_id": 1,
                "question_key": "q_base",
                "enunciado": "Como voce avalia sua base em Matematica?",
                "question_type": "intensidade_1_5",
                "allows_multiple": 0,
                "affect_id": 10,
                "weight": 1.0,
                "impact_type": "sum",
                "affect_active": 1,
                "metric_key": "mathematical_foundation_score",
                "option_value": None,
                "option_label": None,
            },
            {
                "question_id": 2,
                "question_key": "q_autonomia",
                "enunciado": "Qual seu nivel de autonomia?",
                "question_type": "intensidade_1_5",
                "allows_multiple": 0,
                "affect_id": 11,
                "weight": 1.0,
                "impact_type": "sum",
                "affect_active": 1,
                "metric_key": "autonomy_score",
                "option_value": None,
                "option_label": None,
            },
            {
                "question_id": 3,
                "question_key": "q_dificuldades",
                "enunciado": "Quais conteudos voce sente mais dificuldade?",
                "question_type": "multipla_escolha",
                "allows_multiple": 1,
                "affect_id": 12,
                "weight": 1.0,
                "impact_type": "sum",
                "affect_active": 1,
                "metric_key": "mathematical_foundation_score",
                "option_value": "algebra",
                "option_label": "Algebra",
            },
            {
                "question_id": 4,
                "question_key": "q_ansiedade",
                "enunciado": "Como voce se sente antes de provas?",
                "question_type": "intensidade_1_5",
                "allows_multiple": 0,
                "affect_id": 13,
                "weight": 1.0,
                "impact_type": "risk",
                "affect_active": 1,
                "metric_key": "risk_score",
                "option_value": None,
                "option_label": None,
            },
        ]


def test_generate_metrics_uses_database_rules_when_structured_answers_are_available() -> None:
    service = MetricsService(database_repository=FakeMetricsRepository())

    metrics = service.generate_metrics(
        educational_form_responses=[
            QuestionAnswerContext(
                question_key="q_base",
                question_type="intensidade_1_5",
                question="Como voce avalia sua base em Matematica?",
                answer="4",
                answer_values=["4"],
            ),
            QuestionAnswerContext(
                question_key="q_autonomia",
                question_type="intensidade_1_5",
                question="Qual seu nivel de autonomia?",
                answer="5",
                answer_values=["5"],
            ),
            QuestionAnswerContext(
                question_key="q_dificuldades",
                question_type="multipla_escolha",
                question="Quais conteudos voce sente mais dificuldade?",
                answer="Algebra",
                answer_values=["algebra"],
            ),
            QuestionAnswerContext(
                question_key="q_ansiedade",
                question_type="intensidade_1_5",
                question="Como voce se sente antes de provas?",
                answer="5",
                answer_values=["5"],
            ),
        ],
    )

    assert metrics.mathematical_foundation_score == 88
    assert metrics.autonomy_score == 100
    assert metrics.risk_score == 0
    assert metrics.general_readiness_score == 50


def test_generate_metrics_infers_low_autonomy_and_high_risk_from_negative_context() -> None:
    service = MetricsService(database_repository=FakeMetricsRepository())

    metrics = service.generate_metrics(
        educational_form_responses=[
            QuestionAnswerContext(
                question="Quais sao suas maiores dificuldades?",
                answer="Estou perdido, procrastino muito e tenho dificuldade em algebra e funcoes.",
            )
        ],
    )

    assert metrics.model_dump() == {
        "risk_score": 50,
        "general_readiness_score": 50,
        "mathematical_foundation_score": 50,
        "autonomy_score": 50,
    }


def test_generate_metrics_returns_neutral_scores_when_database_has_no_matching_rules() -> None:
    service = MetricsService(database_repository=FakeMetricsRepository())

    metrics = service.generate_metrics(
        educational_form_responses=[
            QuestionAnswerContext(
                question="Como voce estuda?",
                answer="Tenho rotina, estudo sozinho, mas estou um pouco travado com a base.",
            )
        ],
    )

    assert metrics.model_dump() == {
        "risk_score": 50,
        "general_readiness_score": 50,
        "mathematical_foundation_score": 50,
        "autonomy_score": 50,
    }


def test_generate_metrics_returns_neutral_scores_when_called_without_context() -> None:
    service = MetricsService()

    metrics = service.generate_metrics()

    assert metrics.model_dump() == {
        "risk_score": 50,
        "general_readiness_score": 50,
        "mathematical_foundation_score": 50,
        "autonomy_score": 50,
    }

import logging
import unicodedata

from app.schemas.route import QuestionAnswerContext, StudentMetrics

logger = logging.getLogger(__name__)


class MetricsService:
    _NEUTRAL_SCORE = 50

    _DIMENSION_SIGNALS: dict[str, tuple[tuple[str, int], ...]] = {
        "general_readiness_score": (
            ("entendo", 10),
            ("consigo acompanhar", 12),
            ("consigo estudar", 8),
            ("ja estudei", 8),
            ("pratico", 6),
            ("reviso", 6),
            ("tenho base", 10),
            ("tenho dificuldade", -16),
            ("estou perdido", -18),
            ("nao entendo", -18),
            ("tenho duvida", -8),
            ("muita duvida", -12),
            ("confuso", -12),
            ("travado", -14),
        ),
        "mathematical_foundation_score": (
            ("algebra", 8),
            ("funcoes", 8),
            ("equacoes", 8),
            ("geometria", 6),
            ("estatistica", 6),
            ("calculo", 6),
            ("domino algebra", 14),
            ("tenho base em algebra", 16),
            ("tenho dificuldade em algebra", -20),
            ("tenho dificuldade em funcoes", -20),
            ("tenho dificuldade em matematica", -22),
            ("fracao", -10),
            ("fractions", -10),
            ("erro conta", -12),
            ("base fraca", -18),
            ("lacuna", -12),
        ),
        "autonomy_score": (
            ("rotina", 12),
            ("planejo", 10),
            ("organizado", 12),
            ("organizada", 12),
            ("constancia", 10),
            ("estudo sozinho", 16),
            ("consigo sozinho", 14),
            ("anoto", 6),
            ("procrastino", -18),
            ("desorganizado", -18),
            ("desorganizada", -18),
            ("nao consigo estudar sozinho", -22),
            ("dependo", -10),
            ("sem rotina", -18),
            ("falta de disciplina", -18),
        ),
        "risk_score": (
            ("ansioso", 16),
            ("ansiedade", 18),
            ("desmotivado", 18),
            ("desmotivada", 18),
            ("sobrecarregado", 18),
            ("sobrecarregada", 18),
            ("sem tempo", 16),
            ("procrastino", 12),
            ("estou perdido", 18),
            ("travado", 14),
            ("travada", 14),
            ("muita dificuldade", 14),
            ("nao entendo", 16),
            ("confiante", -16),
            ("consigo acompanhar", -12),
            ("rotina", -8),
            ("organizado", -8),
            ("organizada", -8),
            ("pratico", -6),
        ),
    }

    def generate_metrics(
        self,
        educational_form_responses: list[QuestionAnswerContext] | None = None,
    ) -> StudentMetrics:
        responses = list(educational_form_responses or [])
        inferred_scores = self._infer_scores(responses=responses)
        generated_metrics = StudentMetrics(**inferred_scores)

        logger.info(
            "student_metrics_generated response_count=%s generated_metrics=%s",
            len(responses),
            generated_metrics.model_dump(exclude_none=True),
        )
        return generated_metrics

    def _infer_scores(
        self,
        responses: list[QuestionAnswerContext],
    ) -> dict[str, int]:
        combined_segments = []
        combined_segments.extend(response.question for response in responses)
        combined_segments.extend(response.answer for response in responses)
        normalized_text = self._normalize_text(" ".join(combined_segments))

        scores = {
            field_name: self._score_dimension(normalized_text, field_name)
            for field_name in StudentMetrics.model_fields
        }

        if responses:
            scores["general_readiness_score"] = self._clamp(scores["general_readiness_score"] + min(len(responses) * 2, 8))
            scores["autonomy_score"] = self._clamp(scores["autonomy_score"] + min(len(responses), 5))

        if not normalized_text.strip():
            return {field_name: self._NEUTRAL_SCORE for field_name in StudentMetrics.model_fields}

        support_gap = round(
            (
                (100 - scores["general_readiness_score"]) * 0.35
                + (100 - scores["mathematical_foundation_score"]) * 0.35
                + (100 - scores["autonomy_score"]) * 0.30
            )
        )
        scores["risk_score"] = self._clamp(round((scores["risk_score"] * 0.55) + (support_gap * 0.45)))
        return scores

    def _score_dimension(self, normalized_text: str, field_name: str) -> int:
        score = self._NEUTRAL_SCORE
        for term, weight in self._DIMENSION_SIGNALS[field_name]:
            if term in normalized_text:
                score += weight
        return self._clamp(score)

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(char for char in normalized if not unicodedata.combining(char)).lower()

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

import logging
import unicodedata

from app.repositories.database_repository import DatabaseRepository
from app.schemas.route import QuestionAnswerContext, StudentMetrics

logger = logging.getLogger(__name__)


class MetricsService:
    _NEUTRAL_SCORE = 50

    def __init__(self, database_repository: DatabaseRepository | None = None):
        self.database_repository = database_repository or DatabaseRepository()

    def generate_metrics(
        self,
        educational_form_responses: list[QuestionAnswerContext] | None = None,
    ) -> StudentMetrics:
        responses = list(educational_form_responses or [])
        generated_metrics = self._generate_metrics_from_database(responses)
        if generated_metrics is None:
            generated_metrics = self._neutral_metrics()

        logger.info(
            "student_metrics_generated response_count=%s generated_metrics=%s",
            len(responses),
            generated_metrics.model_dump(exclude_none=True),
        )
        return generated_metrics

    def _generate_metrics_from_database(
        self,
        responses: list[QuestionAnswerContext],
    ) -> StudentMetrics | None:
        if not responses:
            return None

        try:
            metric_keys = self.database_repository.fetch_active_metric_keys()
            rules = self.database_repository.fetch_question_metric_rules(
                question_keys=[response.question_key or "" for response in responses],
                question_texts=[response.question for response in responses],
            )
        except Exception as exc:
            logger.warning("database_metric_generation_unavailable error=%s", exc)
            return None

        if not metric_keys or not rules:
            return None

        rules_by_question = self._group_rules_by_question(rules)
        accumulators: dict[str, dict[str, float]] = {}

        for response in responses:
            question_rule = self._match_question_rule(response, rules_by_question)
            if question_rule is None:
                continue

            answer_values = self._resolve_answer_values(response, question_rule)
            if not answer_values:
                continue

            for affect in question_rule["affects"]:
                if not affect["metric_key"] or not affect["active"]:
                    continue

                selected_option_value = affect["option_value"]
                if selected_option_value and selected_option_value not in answer_values:
                    continue

                weight = affect["weight"]
                if weight <= 0:
                    continue

                score = self._resolve_affect_score(
                    question_type=question_rule["question_type"],
                    answer_values=answer_values,
                    impact_type=affect["impact_type"],
                )
                bucket = accumulators.setdefault(affect["metric_key"], {"weighted_sum": 0.0, "weight_total": 0.0})
                bucket["weighted_sum"] += score * weight
                bucket["weight_total"] += weight

        if not accumulators:
            return None

        scores = {metric_key: self._NEUTRAL_SCORE for metric_key in StudentMetrics.model_fields}
        for metric_key, bucket in accumulators.items():
            weight_total = bucket["weight_total"]
            if weight_total <= 0:
                continue
            scores[metric_key] = self._clamp(round(bucket["weighted_sum"] / weight_total))

        for metric_key in metric_keys:
            scores.setdefault(metric_key, self._NEUTRAL_SCORE)

        return StudentMetrics(**scores)

    def _neutral_metrics(self) -> StudentMetrics:
        return StudentMetrics(
            **{field_name: self._NEUTRAL_SCORE for field_name in StudentMetrics.model_fields}
        )

    def _group_rules_by_question(self, rows: list[dict]) -> dict[str, dict[str, object]]:
        grouped: dict[str, dict[str, object]] = {}
        for row in rows:
            question_key = str(row.get("question_key") or "")
            question_text = str(row.get("enunciado") or "")
            question_id = str(row.get("question_id") or question_key or question_text)
            entry = grouped.setdefault(
                question_id,
                {
                    "question_key": question_key,
                    "question_text": question_text,
                    "question_type": str(row.get("question_type") or ""),
                    "allows_multiple": bool(row.get("allows_multiple")),
                    "affects": [],
                },
            )
            if row.get("affect_id") is None:
                continue
            entry["affects"].append(
                {
                    "metric_key": str(row.get("metric_key") or ""),
                    "option_value": str(row.get("option_value") or ""),
                    "option_label": str(row.get("option_label") or ""),
                    "impact_type": str(row.get("impact_type") or "sum"),
                    "weight": float(row.get("weight") or 0),
                    "active": int(row.get("affect_active") or 0) == 1,
                }
            )
        return grouped

    def _match_question_rule(
        self,
        response: QuestionAnswerContext,
        rules_by_question: dict[str, dict[str, object]],
    ) -> dict[str, object] | None:
        normalized_key = (response.question_key or "").strip()
        normalized_question = self._normalize_text(response.question)

        for question_rule in rules_by_question.values():
            if normalized_key and normalized_key == question_rule["question_key"]:
                return question_rule
            if normalized_question and normalized_question == self._normalize_text(str(question_rule["question_text"])):
                return question_rule
        return None

    def _resolve_answer_values(
        self,
        response: QuestionAnswerContext,
        question_rule: dict[str, object],
    ) -> list[str]:
        explicit_values = [value.strip() for value in response.answer_values if value.strip()]
        if explicit_values:
            return explicit_values

        question_type = str(question_rule["question_type"])
        if question_type == "dissertativa":
            return [response.answer.strip()] if response.answer.strip() else []
        if question_type == "intensidade_1_5":
            return [response.answer.strip()] if response.answer.strip() else []

        normalized_answer = self._normalize_text(response.answer)
        matched_values: list[str] = []
        for affect in question_rule["affects"]:
            option_value = str(affect["option_value"])
            option_label = str(affect["option_label"])
            if not option_value:
                continue
            normalized_label = self._normalize_text(option_label)
            normalized_value = self._normalize_text(option_value)
            if normalized_label and normalized_label in normalized_answer:
                matched_values.append(option_value)
            elif normalized_value and normalized_value in normalized_answer:
                matched_values.append(option_value)

        unique_values: list[str] = []
        for value in matched_values:
            if value not in unique_values:
                unique_values.append(value)
        return unique_values

    def _resolve_affect_score(self, *, question_type: str, answer_values: list[str], impact_type: str) -> float:
        normalized_impact = impact_type.strip().lower()

        if question_type == "dissertativa":
            return 100.0

        if question_type == "intensidade_1_5":
            try:
                value = int(answer_values[0])
            except (IndexError, TypeError, ValueError):
                value = 0
            value = max(1, min(5, value))
            score = ((value - 1) / 4) * 100
            if normalized_impact in {"inverse", "inverse_scale", "risk"}:
                return 100.0 - score
            return score

        if question_type == "multipla_escolha":
            if normalized_impact in {"inverse", "inverse_scale", "risk"}:
                return 0.0
            return 100.0

        return float(self._NEUTRAL_SCORE)

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(char for char in normalized if not unicodedata.combining(char)).lower()

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

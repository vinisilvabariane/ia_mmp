from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudentMetrics(BaseModel):
    risk_score: int | None = Field(default=None, ge=0, le=100)
    general_readiness_score: int | None = Field(default=None, ge=0, le=100)
    mathematical_foundation_score: int | None = Field(default=None, ge=0, le=100)
    autonomy_score: int | None = Field(default=None, ge=0, le=100)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def normalize_numeric_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        for field_name in (
            "risk_score",
            "general_readiness_score",
            "mathematical_foundation_score",
            "autonomy_score",
        ):
            raw_value = normalized.get(field_name)
            if raw_value in (None, ""):
                continue

            try:
                numeric_value = round(float(raw_value))
            except (TypeError, ValueError):
                continue

            normalized[field_name] = max(0, min(100, int(numeric_value)))

        return normalized


class QuestionAnswerContext(BaseModel):
    question_key: str | None = None
    question_type: str | None = None
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    answer_values: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        normalized = dict(value)
        raw_answer = normalized.get("answer")
        raw_answer_values = normalized.get("answer_values")

        answer_values: list[str] = []
        if isinstance(raw_answer_values, list):
            answer_values.extend(
                str(item).strip()
                for item in raw_answer_values
                if str(item).strip()
            )
        elif raw_answer_values is not None and str(raw_answer_values).strip():
            answer_values.append(str(raw_answer_values).strip())

        if isinstance(raw_answer, list):
            answer_values.extend(
                str(item).strip()
                for item in raw_answer
                if str(item).strip()
            )
            normalized["answer"] = ", ".join(answer_values)
        elif raw_answer is None:
            normalized["answer"] = ", ".join(answer_values)
        else:
            normalized["answer"] = str(raw_answer).strip()
            if not answer_values and normalized["answer"]:
                answer_values.append(normalized["answer"])

        unique_answer_values: list[str] = []
        for item in answer_values:
            if item not in unique_answer_values:
                unique_answer_values.append(item)
        normalized["answer_values"] = unique_answer_values
        return normalized


class GenerateRouteRequest(BaseModel):
    question: str = Field(..., min_length=1)
    student_metrics: StudentMetrics | None = None
    educational_form_responses: list[QuestionAnswerContext] = Field(default_factory=list)


class GenerateMetricsRequest(BaseModel):
    educational_form_responses: list[QuestionAnswerContext] = Field(..., min_length=1)


class ResourceQuerySet(BaseModel):
    videos_query: str | None = None
    literature_query: str | None = None
    disciplines_query: str | None = None


class ResourceReference(BaseModel):
    kind: Literal["discipline", "video", "literature"]
    title: str
    reason: str
    url: str | None = None
    source: str | None = None
    topic: str | None = None
    difficulty: str | int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RouteDiagnosis(BaseModel):
    risk_score: int | None = None
    general_readiness_score: int | None = None
    mathematical_foundation_score: int | None = None
    autonomy_score: int | None = None
    support_level: str
    starting_level: str
    pace: str
    confidence_note: str
    summary: str


class LearningStage(BaseModel):
    stage_number: int
    title: str
    objective: str
    content_focus: list[str]
    study_actions: list[str]
    estimated_hours: int = Field(..., ge=1)
    advancement_criteria: str
    if_struggling: str
    if_excelling: str
    resources: list[ResourceReference] = Field(default_factory=list)


class RouteCheckpoint(BaseModel):
    name: str
    when: str
    success_signals: list[str]
    if_not_ready: list[str]


class PrioritizedResources(BaseModel):
    disciplines: list[ResourceReference] = Field(default_factory=list)
    videos: list[ResourceReference] = Field(default_factory=list)
    literature: list[ResourceReference] = Field(default_factory=list)
    study_strategies: list[str] = Field(default_factory=list)


class AlternativePlan(BaseModel):
    if_blocked: str
    if_ahead: str
    minimum_viable_plan: str


class LearningRoute(BaseModel):
    question: str
    diagnosis: RouteDiagnosis
    central_goal: str
    starting_point: str
    route_intensity: str
    suggested_schedule: str
    stages: list[LearningStage]
    checkpoints: list[RouteCheckpoint]
    alternative_plan: AlternativePlan
    prioritized_resources: PrioritizedResources
    generated_queries: ResourceQuerySet
    raw_context: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class GenerateRouteResponse(BaseModel):
    route: LearningRoute


class ExplainRouteRequest(BaseModel):
    route: LearningRoute


class ExplainRouteResponse(BaseModel):
    explanation: str

import json
import logging
import re
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_groq import ChatGroq

from app.core.config import LLM_MAX_RETRIES, LLM_MODEL, LLM_TIMEOUT_SECONDS, SQL_SEARCH_LIMIT
from app.core.errors import DependencyAppError, RouteGenerationError, SQLGenerationError
from app.core.prompts import SQL_GENERATION_PROMPT
from app.repositories.database_repository import DatabaseRepository
from app.schemas.route import LearningRoute, ResourceQuerySet, StudentMetrics
from app.services.route_builder import LearningRouteBuilder
from app.services.route_renderer import RouteRenderer

logger = logging.getLogger(__name__)


class RagService:
    def __init__(
        self,
        database_repository: DatabaseRepository | None = None,
        route_builder: LearningRouteBuilder | None = None,
        route_renderer: RouteRenderer | None = None,
    ):
        self.database_repository = database_repository or DatabaseRepository()
        self.route_builder = route_builder or LearningRouteBuilder()
        self.route_renderer = route_renderer or RouteRenderer()

    def generate_route(self, question: str, student_metrics: StudentMetrics | None) -> LearningRoute:
        metrics = student_metrics or StudentMetrics()
        queries = self.build_sql_queries(question=question, student_metrics=metrics)
        results = self.database_repository.execute_resource_queries(
            queries=queries.model_dump(),
            limit=SQL_SEARCH_LIMIT,
        )
        try:
            return self.route_builder.build(
                question=question,
                metrics=metrics,
                queries=queries,
                resources=results,
            )
        except Exception as exc:
            logger.exception("route_builder_failed question=%s", question)
            raise RouteGenerationError("Falha ao montar a rota de aprendizagem.") from exc

    def explain_route(self, route: LearningRoute) -> str:
        return self.route_renderer.render(route)

    def ask(self, question: str, student_metrics: StudentMetrics | None) -> str:
        route = self.generate_route(question=question, student_metrics=student_metrics)
        return self.explain_route(route)

    def build_sql_queries(self, question: str, student_metrics: StudentMetrics) -> ResourceQuerySet:
        sql_prompt = ChatPromptTemplate.from_template(SQL_GENERATION_PROMPT)
        llm = self._build_llm()
        raw_response = (
            sql_prompt
            | llm
            | StrOutputParser()
            | RunnableLambda(self.clean_response)
        ).invoke(
            {
                "question": question,
                "student_metrics": json.dumps(student_metrics.model_dump(exclude_none=True), ensure_ascii=True, indent=2),
                "sql_limit": SQL_SEARCH_LIMIT,
            }
        )

        try:
            parsed_response = self.parse_sql_queries(raw_response)
            query_set = ResourceQuerySet.model_validate(parsed_response)
        except Exception as exc:
            logger.exception("sql_query_parse_failed response=%s", raw_response)
            raise SQLGenerationError("Falha ao interpretar as queries SQL geradas pela LLM.") from exc

        logger.info(
            "sql_queries_generated question=%s has_videos=%s has_literature=%s has_disciplines=%s",
            question,
            bool(query_set.videos_query),
            bool(query_set.literature_query),
            bool(query_set.disciplines_query),
        )
        return query_set

    def parse_sql_queries(self, raw_response: str) -> dict[str, str | None]:
        normalized_response = raw_response.strip()
        if normalized_response.startswith("```"):
            normalized_response = re.sub(r"^```(?:json)?", "", normalized_response).strip()
            normalized_response = re.sub(r"```$", "", normalized_response).strip()

        parsed = json.loads(normalized_response)
        if not isinstance(parsed, dict):
            raise ValueError("O gerador de SQL deve retornar um objeto JSON.")
        return parsed

    def clean_response(self, text: str) -> str:
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _build_llm(self) -> ChatGroq:
        try:
            return ChatGroq(
                model_name=LLM_MODEL,
                temperature=0,
                timeout=LLM_TIMEOUT_SECONDS,
                max_retries=LLM_MAX_RETRIES,
            )
        except TypeError:
            logger.warning("chatgroq_timeout_retry_unsupported model=%s", LLM_MODEL)
            try:
                return ChatGroq(model_name=LLM_MODEL, temperature=0)
            except Exception as exc:
                raise DependencyAppError("Falha ao inicializar o cliente da LLM.") from exc
        except Exception as exc:
            raise DependencyAppError("Falha ao inicializar o cliente da LLM.") from exc

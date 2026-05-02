from app.schemas.route import QuestionAnswerContext, ResourceQuerySet, StudentMetrics
from app.services.rag_service import RagService


class StubRepository:
    def execute_resource_queries(self, queries: dict[str, str | None], limit: int) -> dict[str, list[dict[str, object]]]:
        return {
            "disciplines_query": [
                {
                    "name": "Calculo I",
                    "department": "Matematica",
                    "difficulty_level": 5,
                    "syllabus": "Limites, derivadas e integrais",
                }
            ],
            "videos_query": [
                {
                    "title": "Calculo 1 - Professor Leonard",
                    "topic": "Matematica - Calculo",
                    "difficulty_level": 3,
                    "url": "https://example.com/video",
                    "source": "YouTube",
                }
            ],
            "literature_query": [],
        }


def test_generate_route_uses_llm_route_payload_when_available(monkeypatch) -> None:
    service = RagService(database_repository=StubRepository())

    monkeypatch.setattr(
        service,
        "build_sql_queries",
        lambda **_kwargs: ResourceQuerySet(
            disciplines_query="SELECT * FROM disciplines LIMIT 3",
            videos_query="SELECT * FROM videos LIMIT 3",
            literature_query="SELECT * FROM literature LIMIT 3",
        ),
    )
    monkeypatch.setattr(
        service,
        "build_route_payload",
        lambda **_kwargs: {
            "question": "Texto antigo",
            "diagnosis": {
                "support_level": "moderada",
                "starting_level": "revisao guiada com pratica",
                "pace": "ritmo equilibrado com revisao semanal",
                "confidence_note": "Gerado pela LLM.",
                "summary": "Resumo gerado pela LLM.",
            },
            "central_goal": "Dominar calculo diferencial",
            "starting_point": "revisao guiada com pratica",
            "route_intensity": "moderada",
            "suggested_schedule": "3 semanas, 3 blocos, 5 horas por semana",
            "stages": [
                {
                    "stage_number": 1,
                    "title": "Revisao guiada",
                    "objective": "Fortalecer pre-requisitos.",
                    "content_focus": ["algebra", "funcoes"],
                    "study_actions": ["Resolver exercicios basicos."],
                    "estimated_hours": 2,
                    "advancement_criteria": "Acertar exercicios iniciais.",
                    "if_struggling": "Voltar para algebra.",
                    "if_excelling": "Avancar para limites.",
                    "resources": [
                        {"title": "Calculo 1 - Professor Leonard", "reason": "Video principal."}
                    ],
                },
                {
                    "stage_number": 2,
                    "title": "Pratica",
                    "objective": "Ganhar fluidez.",
                    "content_focus": ["limites"],
                    "study_actions": ["Praticar diariamente."],
                    "estimated_hours": 3,
                    "advancement_criteria": "Resolver problemas basicos.",
                    "if_struggling": "Reduzir a dificuldade.",
                    "if_excelling": "Aumentar a complexidade.",
                    "resources": [],
                },
                {
                    "stage_number": 3,
                    "title": "Aplicacao",
                    "objective": "Consolidar o aprendizado.",
                    "content_focus": ["derivadas"],
                    "study_actions": ["Resolver lista final."],
                    "estimated_hours": 3,
                    "advancement_criteria": "Explicar o processo completo.",
                    "if_struggling": "Revisar a etapa anterior.",
                    "if_excelling": "Adicionar exercicios extras.",
                    "resources": [],
                },
            ],
            "checkpoints": [
                {
                    "name": "Checkpoint 1",
                    "when": "Semana 1",
                    "success_signals": ["Entende limites."],
                    "if_not_ready": ["Revisar funcoes."],
                },
                {
                    "name": "Checkpoint 2",
                    "when": "Semana 2",
                    "success_signals": ["Resolve exercicios intermediarios."],
                    "if_not_ready": ["Voltar para listas guiadas."],
                },
            ],
            "alternative_plan": {
                "if_blocked": "Reduzir o escopo.",
                "if_ahead": "Aprofundar com novos problemas.",
                "minimum_viable_plan": "Estudar diariamente em blocos curtos.",
            },
            "prioritized_resources": {
                "disciplines": [],
                "videos": [{"title": "Calculo 1 - Professor Leonard", "reason": "Video principal."}],
                "literature": [],
                "study_strategies": ["Estudar em blocos curtos."],
            },
            "generated_queries": {},
            "raw_context": {},
        },
    )

    route = service.generate_route(
        question="Como estudar calculo?",
        student_metrics=StudentMetrics(
            risk_score=75,
            general_readiness_score=42,
            mathematical_foundation_score=30,
            autonomy_score=35,
        ),
        educational_form_responses=[
            QuestionAnswerContext(question="Maior dificuldade?", answer="Algebra e funcoes.")
        ],
    )

    assert route.question == "Como estudar calculo?"
    assert route.central_goal == "Dominar calculo diferencial"
    assert route.stages[0].title == "Revisao guiada"
    assert route.stages[0].resources[0].title == "Calculo 1 - Professor Leonard"


def test_generate_route_falls_back_to_heuristic_when_llm_route_fails(monkeypatch) -> None:
    service = RagService(database_repository=StubRepository())

    monkeypatch.setattr(
        service,
        "build_sql_queries",
        lambda **_kwargs: ResourceQuerySet(
            disciplines_query="SELECT * FROM disciplines LIMIT 3",
            videos_query="SELECT * FROM videos LIMIT 3",
            literature_query="SELECT * FROM literature LIMIT 3",
        ),
    )
    monkeypatch.setattr(service, "build_route_payload", lambda **_kwargs: (_ for _ in ()).throw(ValueError("falhou")))

    route = service.generate_route(
        question="Como estudar calculo?",
        student_metrics=StudentMetrics(
            risk_score=75,
            general_readiness_score=42,
            mathematical_foundation_score=30,
            autonomy_score=35,
        ),
    )

    assert route.starting_point == "fundamentos e prerequisitos"
    assert route.route_intensity == "alta"

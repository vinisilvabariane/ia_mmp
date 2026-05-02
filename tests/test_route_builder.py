from app.schemas.route import ResourceQuerySet, StudentMetrics
from app.services.route_builder import LearningRouteBuilder


def test_route_builder_creates_structured_route() -> None:
    builder = LearningRouteBuilder()
    route = builder.build(
        question="Como estudar calculo?",
        metrics=StudentMetrics(
            risk_score=75,
            general_readiness_score=42,
            mathematical_foundation_score=30,
            autonomy_score=35,
        ),
        queries=ResourceQuerySet(
            disciplines_query="SELECT * FROM disciplines LIMIT 3",
            videos_query="SELECT * FROM videos LIMIT 3",
            literature_query="SELECT * FROM literature LIMIT 3",
        ),
        resources={
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
            "literature_query": [
                {
                    "title": "Algorithm Unlocked",
                    "topic": "Algoritmos",
                    "level": "Iniciante",
                    "url": "https://example.com/book",
                    "institution": "MIT Press",
                }
            ],
        },
    )

    assert route.starting_point == "fundamentos e prerequisitos"
    assert route.route_intensity == "alta"
    assert len(route.stages) == 3
    assert route.prioritized_resources.videos[0].title == "Calculo 1 - Professor Leonard"


def test_route_builder_normalizes_sparse_llm_route_payload() -> None:
    builder = LearningRouteBuilder()
    normalized_route = builder.normalize_llm_route(
        route_payload={
            "question": "Texto incorreto",
            "diagnosis": {
                "support_level": "moderada",
                "starting_level": "revisao guiada com pratica",
                "pace": "ritmo equilibrado com revisao semanal",
                "confidence_note": "Gerado com base no contexto.",
                "summary": "Resumo curto.",
            },
            "central_goal": "Dominar calculo diferencial",
            "stages": [
                {
                    "stage_number": 1,
                    "title": "Base",
                    "objective": "Revisar pre-requisitos.",
                    "content_focus": ["algebra", "funcoes"],
                    "study_actions": ["Resolver exercicios basicos."],
                    "estimated_hours": 2,
                    "advancement_criteria": "Acertar exercicios iniciais.",
                    "if_struggling": "Voltar para algebra.",
                    "if_excelling": "Avancar para limites.",
                    "resources": [
                        {
                            "title": "Calculo 1 - Professor Leonard",
                            "reason": "Bom para revisar a base.",
                        }
                    ],
                }
            ],
            "checkpoints": [
                {
                    "name": "Checkpoint personalizado",
                    "when": "Fim da primeira semana",
                    "success_signals": ["Consegue explicar limites."],
                    "if_not_ready": ["Rever funcoes."],
                }
            ],
            "alternative_plan": {
                "if_blocked": "Diminuir o escopo.",
                "if_ahead": "Adicionar exercicios extras.",
                "minimum_viable_plan": "Estudar 30 min por dia.",
            },
            "prioritized_resources": {
                "videos": [
                    {
                        "title": "Calculo 1 - Professor Leonard",
                        "reason": "Video central.",
                    }
                ],
                "study_strategies": ["Estudar em blocos curtos."],
            },
        },
        question="Como estudar calculo?",
        metrics=StudentMetrics(
            risk_score=75,
            general_readiness_score=42,
            mathematical_foundation_score=30,
            autonomy_score=35,
        ),
        queries=ResourceQuerySet(
            disciplines_query="SELECT * FROM disciplines LIMIT 3",
            videos_query="SELECT * FROM videos LIMIT 3",
            literature_query="SELECT * FROM literature LIMIT 3",
        ),
        resources={
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
        },
    )

    assert normalized_route.question == "Como estudar calculo?"
    assert normalized_route.generated_queries.videos_query == "SELECT * FROM videos LIMIT 3"
    assert normalized_route.diagnosis.risk_score == 75
    assert len(normalized_route.stages) >= 3
    assert normalized_route.stages[0].resources[0].title == "Calculo 1 - Professor Leonard"

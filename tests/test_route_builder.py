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

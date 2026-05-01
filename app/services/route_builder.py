import unicodedata
from typing import Any

from app.schemas.route import (
    AlternativePlan,
    LearningRoute,
    LearningStage,
    PrioritizedResources,
    ResourceQuerySet,
    ResourceReference,
    RouteCheckpoint,
    RouteDiagnosis,
    StudentMetrics,
)


def _score_band(score: int | None, *, invert: bool = False) -> str:
    if score is None:
        return "unknown"
    if score >= 70:
        return "low" if invert else "high"
    if score >= 40:
        return "medium"
    return "high" if invert else "low"


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).lower()


class LearningRouteBuilder:
    def build(
        self,
        question: str,
        metrics: StudentMetrics,
        queries: ResourceQuerySet,
        resources: dict[str, list[dict[str, Any]]],
    ) -> LearningRoute:
        diagnosis = self._build_diagnosis(metrics)
        prioritized_resources = self._build_prioritized_resources(question, diagnosis, resources)
        stages = self._build_stages(question, diagnosis, prioritized_resources)
        checkpoints = self._build_checkpoints(diagnosis)

        return LearningRoute(
            question=question,
            diagnosis=diagnosis,
            central_goal=self._build_central_goal(question),
            starting_point=diagnosis.starting_level,
            route_intensity=diagnosis.support_level,
            suggested_schedule=self._build_schedule(diagnosis),
            stages=stages,
            checkpoints=checkpoints,
            alternative_plan=self._build_alternative_plan(diagnosis),
            prioritized_resources=prioritized_resources,
            generated_queries=queries,
            raw_context=resources,
        )

    def _build_diagnosis(self, metrics: StudentMetrics) -> RouteDiagnosis:
        risk_band = _score_band(metrics.risk_score, invert=True)
        readiness_band = _score_band(metrics.general_readiness_score)
        math_band = _score_band(metrics.mathematical_foundation_score)
        autonomy_band = _score_band(metrics.autonomy_score)

        support_level = "alta"
        if risk_band == "low" and autonomy_band in {"medium", "high"}:
            support_level = "moderada"
        if risk_band == "low" and readiness_band == "high" and autonomy_band == "high":
            support_level = "leve"

        starting_level = "fundamentos e prerequisitos"
        if math_band == "medium" and readiness_band in {"medium", "high"}:
            starting_level = "revisao guiada com pratica"
        if math_band == "high" and readiness_band == "high":
            starting_level = "aplicacao progressiva"

        pace = "passos curtos com checkpoints frequentes"
        if readiness_band == "medium" and autonomy_band in {"medium", "high"}:
            pace = "ritmo equilibrado com revisao semanal"
        if readiness_band == "high" and autonomy_band == "high" and risk_band == "low":
            pace = "ritmo acelerado com aprofundamento opcional"

        confidence_note = (
            "Algumas decisoes usam inferencia conservadora porque nem todas as metricas foram informadas."
            if None in (
                metrics.risk_score,
                metrics.general_readiness_score,
                metrics.mathematical_foundation_score,
                metrics.autonomy_score,
            )
            else "As decisoes foram inferidas diretamente das metricas recebidas."
        )

        summary = (
            f"Risco {risk_band}, prontidao {readiness_band}, base matematica {math_band} "
            f"e autonomia {autonomy_band}. A rota prioriza {starting_level} em {pace}."
        )

        return RouteDiagnosis(
            risk_score=metrics.risk_score,
            general_readiness_score=metrics.general_readiness_score,
            mathematical_foundation_score=metrics.mathematical_foundation_score,
            autonomy_score=metrics.autonomy_score,
            support_level=support_level,
            starting_level=starting_level,
            pace=pace,
            confidence_note=confidence_note,
            summary=summary,
        )

    def _build_prioritized_resources(
        self,
        question: str,
        diagnosis: RouteDiagnosis,
        resources: dict[str, list[dict[str, Any]]],
    ) -> PrioritizedResources:
        focus_terms = self._focus_terms(question, resources)
        disciplines = [
            self._to_resource_reference("discipline", row, focus_terms, diagnosis)
            for row in resources.get("disciplines_query", [])[:3]
        ]
        videos = [
            self._to_resource_reference("video", row, focus_terms, diagnosis)
            for row in resources.get("videos_query", [])[:3]
        ]
        literature = [
            self._to_resource_reference("literature", row, focus_terms, diagnosis)
            for row in resources.get("literature_query", [])[:3]
        ]

        strategies = [
            "Trabalhar em blocos curtos de estudo com registro do que foi entendido e do que travou.",
            "Encerrar cada sessao com um microcheckpoint: resumo proprio, exercicio e duvida aberta.",
        ]
        if diagnosis.support_level == "alta":
            strategies.append("Usar acompanhamento mais frequente, com revisao apos cada etapa.")
        if diagnosis.pace == "ritmo acelerado com aprofundamento opcional":
            strategies.append("Reservar uma sessao semanal para exploracao avancada ou projeto curto.")

        return PrioritizedResources(
            disciplines=disciplines,
            videos=videos,
            literature=literature,
            study_strategies=strategies,
        )

    def _build_stages(
        self,
        question: str,
        diagnosis: RouteDiagnosis,
        prioritized_resources: PrioritizedResources,
    ) -> list[LearningStage]:
        focus = self._build_central_goal(question)
        foundation_resources = prioritized_resources.disciplines[:1] + prioritized_resources.videos[:1]
        practice_resources = prioritized_resources.videos[1:2] + prioritized_resources.literature[:1]
        application_resources = prioritized_resources.disciplines[1:2] + prioritized_resources.literature[1:2]

        stage1 = LearningStage(
            stage_number=1,
            title="Fundamentos e alinhamento",
            objective=f"Consolidar a base necessaria para avancar em {focus}.",
            content_focus=[diagnosis.starting_level, "conceitos nucleares", "prerequisitos"],
            study_actions=[
                "Mapear o que ja domina e o que ainda depende de revisao.",
                "Assistir ao recurso principal e produzir um resumo curto com exemplos proprios.",
                "Resolver exercicios introdutorios antes de partir para novos topicos.",
            ],
            estimated_hours=4 if diagnosis.support_level == "alta" else 3,
            advancement_criteria="Conseguir explicar os conceitos basicos sem consultar o material e acertar exercicios iniciais.",
            if_struggling="Reduzir o escopo, revisar prerequisitos e repetir a pratica com exemplos menores.",
            if_excelling="Aumentar a carga de exercicios e antecipar uma aplicacao simples.",
            resources=foundation_resources,
        )
        stage2 = LearningStage(
            stage_number=2,
            title="Pratica guiada",
            objective="Transformar entendimento conceitual em execucao orientada.",
            content_focus=["exercicios graduais", "resolucao comentada", "feedback rapido"],
            study_actions=[
                "Alternar teoria curta com exercicios de dificuldade crescente.",
                "Registrar erros recorrentes e reestudar apenas os pontos que geraram falha.",
                "Comparar duas solucoes diferentes para o mesmo problema.",
            ],
            estimated_hours=4,
            advancement_criteria="Resolver problemas intermediarios com poucos apoios externos.",
            if_struggling="Voltar ao recurso de base, reduzir a complexidade e inserir um checkpoint extra.",
            if_excelling="Adicionar variacoes de problema ou um mini desafio contextualizado.",
            resources=practice_resources,
        )
        stage3 = LearningStage(
            stage_number=3,
            title="Aplicacao e consolidacao",
            objective="Aplicar o conteudo em contexto e estabilizar a aprendizagem.",
            content_focus=["aplicacao pratica", "autoavaliacao", "consolidacao"],
            study_actions=[
                "Executar uma atividade de aplicacao ligada ao objetivo da pergunta.",
                "Fazer autoavaliacao comparando desempenho atual com o inicio da rota.",
                "Definir proximos topicos de aprofundamento ou revisao.",
            ],
            estimated_hours=5 if diagnosis.pace == "ritmo acelerado com aprofundamento opcional" else 4,
            advancement_criteria="Entregar uma solucao pratica ou explicar o processo completo com clareza.",
            if_struggling="Retornar ao conjunto minimo de exercicios e reduzir a ambicao da aplicacao.",
            if_excelling="Expandir a aplicacao para um caso mais complexo ou interdisciplinar.",
            resources=application_resources,
        )
        return [stage1, stage2, stage3]

    def _build_checkpoints(self, diagnosis: RouteDiagnosis) -> list[RouteCheckpoint]:
        return [
            RouteCheckpoint(
                name="Checkpoint 1",
                when="Ao final da primeira etapa",
                success_signals=[
                    "O estudante consegue resumir os conceitos principais.",
                    "Os erros mais basicos diminuiram.",
                ],
                if_not_ready=[
                    "Repetir a revisao de prerequisitos com carga menor.",
                    "Inserir mais um bloco curto de exercicios guiados.",
                ],
            ),
            RouteCheckpoint(
                name="Checkpoint 2",
                when="Antes da etapa de aplicacao",
                success_signals=[
                    "Ja consegue resolver problemas intermediarios.",
                    "Consegue escolher o recurso certo sem depender de muita orientacao.",
                ],
                if_not_ready=[
                    "Manter pratica guiada por mais uma semana.",
                    "Repriorizar apenas os topicos centrais antes de aprofundar.",
                ],
            ),
        ]

    def _build_alternative_plan(self, diagnosis: RouteDiagnosis) -> AlternativePlan:
        return AlternativePlan(
            if_blocked="Reduzir o objetivo semanal para um unico conceito central, reforcar prerequisitos e encurtar as sessoes.",
            if_ahead="Antecipar um problema de aplicacao, incluir literatura complementar e transformar a etapa final em mini projeto.",
            minimum_viable_plan=(
                "Manter apenas o recurso principal de cada etapa, um exercicio-chave por bloco e um checkpoint semanal."
            ),
        )

    def _build_schedule(self, diagnosis: RouteDiagnosis) -> str:
        if diagnosis.pace == "ritmo acelerado com aprofundamento opcional":
            return "3 semanas, 3 blocos, 6 a 8 horas por semana"
        if diagnosis.support_level == "alta":
            return "4 semanas, 3 blocos, 4 a 6 horas por semana"
        return "3 semanas, 3 blocos, 5 a 6 horas por semana"

    def _build_central_goal(self, question: str) -> str:
        clean_question = question.strip().rstrip("?")
        return clean_question[:1].upper() + clean_question[1:]

    def _focus_terms(self, question: str, resources: dict[str, list[dict[str, Any]]]) -> set[str]:
        terms = {_normalize_text(part) for part in question.split() if len(part) > 3}
        for key in ("disciplines_query", "videos_query", "literature_query"):
            for row in resources.get(key, [])[:2]:
                for field in ("topic", "name", "title"):
                    value = row.get(field)
                    if isinstance(value, str):
                        terms.update(_normalize_text(part) for part in value.split() if len(part) > 3)
        return {term for term in terms if term}

    def _to_resource_reference(
        self,
        kind: str,
        row: dict[str, Any],
        focus_terms: set[str],
        diagnosis: RouteDiagnosis,
    ) -> ResourceReference:
        title = str(row.get("title") or row.get("name") or "Recurso sem titulo")
        topic = row.get("topic") or row.get("department") or row.get("syllabus")
        difficulty = row.get("difficulty_level") or row.get("level")
        title_terms = _normalize_text(title)
        reason = "Apoia diretamente o objetivo principal da rota."
        if any(term in title_terms for term in focus_terms):
            reason = "Tem aderencia direta ao tema pedido pelo estudante."
        elif diagnosis.starting_level == "fundamentos e prerequisitos":
            reason = "Foi priorizado para reforcar base e prerequisitos antes do aprofundamento."
        elif diagnosis.pace == "ritmo acelerado com aprofundamento opcional":
            reason = "Foi mantido por ter potencial de aprofundamento sem perder foco."

        url = row.get("url")
        source = row.get("source") or row.get("institution") or row.get("platform")
        metadata = {
            key: value
            for key, value in row.items()
            if key not in {"title", "name", "url", "source", "institution", "platform", "topic", "department", "syllabus"}
        }
        return ResourceReference(
            kind=kind,
            title=title,
            reason=reason,
            url=str(url) if url else None,
            source=str(source) if source else None,
            topic=str(topic) if topic else None,
            difficulty=difficulty,
            metadata=metadata,
        )

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
        central_goal = self._build_central_goal(question)
        stages = self._build_stages(central_goal, diagnosis, prioritized_resources)
        checkpoints = self._build_checkpoints()

        return LearningRoute(
            question=question,
            diagnosis=diagnosis,
            central_goal=central_goal,
            starting_point=diagnosis.starting_level,
            route_intensity=diagnosis.support_level,
            suggested_schedule=self._build_schedule(diagnosis),
            stages=stages,
            checkpoints=checkpoints,
            alternative_plan=self._build_alternative_plan(),
            prioritized_resources=prioritized_resources,
            generated_queries=queries,
        )

    def normalize_llm_route(
        self,
        route_payload: dict[str, Any],
        question: str,
        metrics: StudentMetrics,
        queries: ResourceQuerySet,
        resources: dict[str, list[dict[str, Any]]],
    ) -> LearningRoute:
        heuristic_route = self.build(
            question=question,
            metrics=metrics,
            queries=queries,
            resources=resources,
        )
        sanitized_payload = dict(route_payload)
        sanitized_payload["question"] = question
        sanitized_payload["generated_queries"] = queries.model_dump()
        sanitized_payload["raw_context"] = resources
        sanitized_payload["central_goal"] = sanitized_payload.get("central_goal") or heuristic_route.central_goal
        sanitized_payload["starting_point"] = sanitized_payload.get("starting_point") or heuristic_route.starting_point
        sanitized_payload["route_intensity"] = sanitized_payload.get("route_intensity") or heuristic_route.route_intensity
        sanitized_payload["suggested_schedule"] = sanitized_payload.get("suggested_schedule") or heuristic_route.suggested_schedule
        sanitized_payload["diagnosis"] = self._merge_diagnosis(
            route_payload.get("diagnosis"),
            metrics,
            heuristic_route.diagnosis,
        )
        sanitized_payload["prioritized_resources"] = self._merge_prioritized_resources(
            route_payload.get("prioritized_resources"),
            heuristic_route.prioritized_resources,
            question,
            resources,
            sanitized_payload["diagnosis"],
        )
        sanitized_payload["alternative_plan"] = self._merge_alternative_plan(
            route_payload.get("alternative_plan"),
            heuristic_route.alternative_plan,
        )
        sanitized_payload["checkpoints"] = self._merge_checkpoints(
            route_payload.get("checkpoints"),
            heuristic_route.checkpoints,
        )
        sanitized_payload["stages"] = self._merge_stages(
            route_payload.get("stages"),
            heuristic_route.stages,
            sanitized_payload["prioritized_resources"],
        )
        return LearningRoute.model_validate(sanitized_payload)

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

    def _merge_diagnosis(
        self,
        diagnosis_payload: Any,
        metrics: StudentMetrics,
        fallback: RouteDiagnosis,
    ) -> dict[str, Any]:
        payload = diagnosis_payload if isinstance(diagnosis_payload, dict) else {}
        return {
            "risk_score": metrics.risk_score,
            "general_readiness_score": metrics.general_readiness_score,
            "mathematical_foundation_score": metrics.mathematical_foundation_score,
            "autonomy_score": metrics.autonomy_score,
            "support_level": payload.get("support_level") or fallback.support_level,
            "starting_level": payload.get("starting_level") or fallback.starting_level,
            "pace": payload.get("pace") or fallback.pace,
            "confidence_note": payload.get("confidence_note") or fallback.confidence_note,
            "summary": payload.get("summary") or fallback.summary,
        }

    def _merge_prioritized_resources(
        self,
        prioritized_payload: Any,
        fallback: PrioritizedResources,
        question: str,
        resources: dict[str, list[dict[str, Any]]],
        diagnosis_payload: dict[str, Any],
    ) -> dict[str, Any]:
        payload = prioritized_payload if isinstance(prioritized_payload, dict) else {}
        diagnosis = RouteDiagnosis.model_validate(diagnosis_payload)
        focus_terms = self._focus_terms(question, resources)
        return {
            "disciplines": self._merge_resource_collection(
                payload.get("disciplines"),
                fallback.disciplines,
                "discipline",
                resources.get("disciplines_query", []),
                focus_terms,
                diagnosis,
            ),
            "videos": self._merge_resource_collection(
                payload.get("videos"),
                fallback.videos,
                "video",
                resources.get("videos_query", []),
                focus_terms,
                diagnosis,
            ),
            "literature": self._merge_resource_collection(
                payload.get("literature"),
                fallback.literature,
                "literature",
                resources.get("literature_query", []),
                focus_terms,
                diagnosis,
            ),
            "study_strategies": self._coerce_string_list(payload.get("study_strategies")) or fallback.study_strategies,
        }

    def _merge_alternative_plan(
        self,
        alternative_payload: Any,
        fallback: AlternativePlan,
    ) -> dict[str, str]:
        payload = alternative_payload if isinstance(alternative_payload, dict) else {}
        return {
            "if_blocked": payload.get("if_blocked") or fallback.if_blocked,
            "if_ahead": payload.get("if_ahead") or fallback.if_ahead,
            "minimum_viable_plan": payload.get("minimum_viable_plan") or fallback.minimum_viable_plan,
        }

    def _merge_checkpoints(
        self,
        checkpoints_payload: Any,
        fallback: list[RouteCheckpoint],
    ) -> list[dict[str, Any]]:
        if not isinstance(checkpoints_payload, list) or not checkpoints_payload:
            return [checkpoint.model_dump() for checkpoint in fallback]

        merged_checkpoints: list[dict[str, Any]] = []
        for index, payload in enumerate(checkpoints_payload):
            fallback_checkpoint = fallback[min(index, len(fallback) - 1)]
            payload = payload if isinstance(payload, dict) else {}
            merged_checkpoints.append(
                {
                    "name": payload.get("name") or fallback_checkpoint.name,
                    "when": payload.get("when") or fallback_checkpoint.when,
                    "success_signals": self._coerce_string_list(payload.get("success_signals")) or fallback_checkpoint.success_signals,
                    "if_not_ready": self._coerce_string_list(payload.get("if_not_ready")) or fallback_checkpoint.if_not_ready,
                }
            )

        if len(merged_checkpoints) < 2:
            merged_checkpoints.extend(
                checkpoint.model_dump() for checkpoint in fallback[len(merged_checkpoints):2]
            )
        return merged_checkpoints

    def _merge_stages(
        self,
        stages_payload: Any,
        fallback: list[LearningStage],
        prioritized_resources_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if not isinstance(stages_payload, list) or not stages_payload:
            return [stage.model_dump() for stage in fallback]

        available_resources = self._resource_lookup_from_prioritized(prioritized_resources_payload)
        merged_stages: list[dict[str, Any]] = []
        for index, payload in enumerate(stages_payload):
            fallback_stage = fallback[min(index, len(fallback) - 1)]
            payload = payload if isinstance(payload, dict) else {}
            merged_stages.append(
                {
                    "stage_number": payload.get("stage_number") or (index + 1),
                    "title": payload.get("title") or fallback_stage.title,
                    "objective": payload.get("objective") or fallback_stage.objective,
                    "content_focus": self._coerce_string_list(payload.get("content_focus")) or fallback_stage.content_focus,
                    "study_actions": self._coerce_string_list(payload.get("study_actions")) or fallback_stage.study_actions,
                    "estimated_hours": self._coerce_positive_int(payload.get("estimated_hours"), fallback_stage.estimated_hours),
                    "advancement_criteria": payload.get("advancement_criteria") or fallback_stage.advancement_criteria,
                    "if_struggling": payload.get("if_struggling") or fallback_stage.if_struggling,
                    "if_excelling": payload.get("if_excelling") or fallback_stage.if_excelling,
                    "resources": self._merge_stage_resources(
                        payload.get("resources"),
                        fallback_stage.resources,
                        available_resources,
                    ),
                }
            )

        if len(merged_stages) < 3:
            merged_stages.extend(stage.model_dump() for stage in fallback[len(merged_stages):3])
        return merged_stages

    def _build_stages(
        self,
        central_goal: str,
        diagnosis: RouteDiagnosis,
        prioritized_resources: PrioritizedResources,
    ) -> list[LearningStage]:
        foundation_resources = prioritized_resources.disciplines[:1] + prioritized_resources.videos[:1]
        practice_resources = prioritized_resources.videos[1:2] + prioritized_resources.literature[:1]
        application_resources = prioritized_resources.disciplines[1:2] + prioritized_resources.literature[1:2]

        stage1 = LearningStage(
            stage_number=1,
            title="Fundamentos e alinhamento",
            objective=f"Consolidar a base necessaria para avancar em {central_goal}.",
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

    def _build_checkpoints(self) -> list[RouteCheckpoint]:
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

    def _build_alternative_plan(self) -> AlternativePlan:
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

    def _merge_resource_collection(
        self,
        resource_payload: Any,
        fallback: list[ResourceReference],
        kind: str,
        source_rows: list[dict[str, Any]],
        focus_terms: set[str],
        diagnosis: RouteDiagnosis,
    ) -> list[dict[str, Any]]:
        fallback_by_title = {item.title: item for item in fallback}
        source_by_title = {
            str(row.get("title") or row.get("name") or "Recurso sem titulo"): row
            for row in source_rows
        }
        merged_items: list[dict[str, Any]] = []

        if isinstance(resource_payload, list):
            for raw_item in resource_payload:
                if not isinstance(raw_item, dict):
                    continue
                title = str(raw_item.get("title") or "")
                fallback_item = fallback_by_title.get(title)
                row = source_by_title.get(title)
                if row is not None:
                    base_item = self._to_resource_reference(kind, row, focus_terms, diagnosis)
                    item_dump = base_item.model_dump()
                    item_dump["reason"] = raw_item.get("reason") or item_dump["reason"]
                    merged_items.append(item_dump)
                elif fallback_item is not None:
                    item_dump = fallback_item.model_dump()
                    item_dump["reason"] = raw_item.get("reason") or item_dump["reason"]
                    merged_items.append(item_dump)

        if merged_items:
            return merged_items[:3]
        return [item.model_dump() for item in fallback]

    def _merge_stage_resources(
        self,
        resource_payload: Any,
        fallback: list[ResourceReference],
        available_resources: dict[str, ResourceReference],
    ) -> list[dict[str, Any]]:
        if not isinstance(resource_payload, list):
            return [item.model_dump() for item in fallback]

        merged_items: list[dict[str, Any]] = []
        for raw_item in resource_payload:
            if not isinstance(raw_item, dict):
                continue
            title = str(raw_item.get("title") or "")
            available_item = available_resources.get(title)
            if available_item is None:
                continue
            item_dump = available_item.model_dump()
            item_dump["reason"] = raw_item.get("reason") or item_dump["reason"]
            merged_items.append(item_dump)

        if merged_items:
            return merged_items
        return [item.model_dump() for item in fallback]

    def _resource_lookup_from_prioritized(
        self,
        prioritized_resources_payload: dict[str, Any],
    ) -> dict[str, ResourceReference]:
        available_resources: dict[str, ResourceReference] = {}
        for key in ("disciplines", "videos", "literature"):
            for item in prioritized_resources_payload.get(key, []):
                resource = ResourceReference.model_validate(item)
                available_resources[resource.title] = resource
        return available_resources

    def _coerce_string_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    def _coerce_positive_int(self, value: Any, fallback: int) -> int:
        try:
            coerced = int(value)
        except (TypeError, ValueError):
            return fallback
        return coerced if coerced >= 1 else fallback

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

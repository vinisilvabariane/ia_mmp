from app.schemas.route import LearningRoute, ResourceReference


class RouteRenderer:
    def render(self, route: LearningRoute) -> str:
        lines: list[str] = []
        diagnosis = route.diagnosis

        lines.extend(
            [
                "DIAGNOSTICO DO MOMENTO",
                f"- Risk score: {self._show_metric(diagnosis.risk_score)}",
                f"- General readiness score: {self._show_metric(diagnosis.general_readiness_score)}",
                f"- Mathematical foundation score: {self._show_metric(diagnosis.mathematical_foundation_score)}",
                f"- Autonomy score: {self._show_metric(diagnosis.autonomy_score)}",
                f"- Leitura pedagogica: {diagnosis.summary}",
                "",
                "OBJETIVO DA ROTA",
                f"- Objetivo central da trilha: {route.central_goal}",
                f"- Ponto de partida recomendado: {route.starting_point}",
                f"- Intensidade da rota: {route.route_intensity}",
                f"- Ritmo sugerido: {route.suggested_schedule}",
                "",
                "ROTA DE APRENDIZAGEM DINAMICA",
            ]
        )

        for stage in route.stages:
            lines.extend(
                [
                    f"{stage.stage_number}. {stage.title}:",
                    f"- Objetivo: {stage.objective}",
                    f"- O que estudar: {', '.join(stage.content_focus)}",
                    f"- Como estudar: {' '.join(stage.study_actions)}",
                    f"- Recursos indicados: {self._join_resource_titles(stage.resources)}",
                    f"- Tempo estimado: {stage.estimated_hours} horas",
                    f"- Criterio para avancar: {stage.advancement_criteria}",
                    f"- Se houver dificuldade: {stage.if_struggling}",
                    f"- Se houver bom desempenho: {stage.if_excelling}",
                    "",
                ]
            )

        lines.append("CHECKPOINTS E AJUSTES")
        for checkpoint in route.checkpoints:
            lines.append(f"- {checkpoint.name}: {checkpoint.when}. Sinais: {'; '.join(checkpoint.success_signals)}")
            lines.append(f"- Se nao estiver pronto: {'; '.join(checkpoint.if_not_ready)}")

        lines.extend(
            [
                "",
                "PLANO ALTERNATIVO",
                f"- Se o aluno travar: {route.alternative_plan.if_blocked}",
                f"- Se o aluno evoluir rapido: {route.alternative_plan.if_ahead}",
                f"- Prioridade minima caso tenha pouco tempo: {route.alternative_plan.minimum_viable_plan}",
                "",
                "RECURSOS PRIORIZADOS",
                f"- Disciplinas: {self._join_resource_titles(route.prioritized_resources.disciplines)}",
                f"- Videos: {self._join_resource_titles(route.prioritized_resources.videos)}",
                f"- Literatura: {self._join_resource_titles(route.prioritized_resources.literature)}",
                f"- Ferramentas ou estrategias de estudo: {'; '.join(route.prioritized_resources.study_strategies)}",
                "",
                "OBSERVACOES FINAIS",
                f"- {diagnosis.confidence_note}",
            ]
        )

        if diagnosis.risk_score is not None and diagnosis.risk_score >= 70:
            lines.append("- O risk score elevado sugere acompanhamento pedagogico mais proximo.")
        if diagnosis.autonomy_score is None:
            lines.append("- O nivel de autonomia nao foi medido diretamente no payload.")

        return "\n".join(lines).strip()

    def _join_resource_titles(self, resources: list[ResourceReference]) -> str:
        if not resources:
            return "Nenhum recurso priorizado."
        return "; ".join(resource.title for resource in resources)

    def _show_metric(self, value: int | None) -> str:
        return str(value) if value is not None else "nao informado"

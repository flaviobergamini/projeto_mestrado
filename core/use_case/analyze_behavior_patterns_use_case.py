from core.kernel.result import Result
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.repositories.beneficiary_repository import BeneficiaryRepository
from infrastructure.services.llm_service import LLMService
from datetime import datetime, timedelta


class AnalyzeBehaviorPatternsUseCase:
    """
    Caso de uso para analisar padrões comportamentais de um beneficiário
    usando registros diários e IA generativa.
    """

    def __init__(
        self,
        diary_repository: DiaryRepository,
        beneficiary_repository: BeneficiaryRepository,
        llm_service: LLMService,
    ):
        self.diary_repository = diary_repository
        self.beneficiary_repository = beneficiary_repository
        self.llm_service = llm_service

    async def execute(
        self, beneficiary_id: int, days: int = 30, analysis_type: str = "comprehensive"
    ):
        """
        Analisa padrões comportamentais de um beneficiário.

        Args:
            beneficiary_id: ID do beneficiário
            days: Número de dias a analisar (padrão 30)
            analysis_type: Tipo de análise (comprehensive, crisis, progress)
        """
        try:
            # Verificar se o beneficiário existe
            beneficiary = await self.beneficiary_repository.get_by_id(beneficiary_id)
            if not beneficiary:
                return Result.not_found("Beneficiário não encontrado")

            # Buscar registros recentes
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)

            diaries = await self.diary_repository.get_by_beneficiary_date_range(
                beneficiary_id, start_date, end_date
            )

            if not diaries:
                return Result.ok({
                    "message": f"Não há registros diários nos últimos {days} dias para análise.",
                    "beneficiary_name": beneficiary.name
                })

            # Configurar LLM com Gemini
            self.llm_service.configure("gemini")

            # Criar resumo estruturado dos registros
            diary_summaries = self._create_diary_summaries(diaries)

            # Selecionar prompt baseado no tipo de análise
            prompt = self._get_analysis_prompt(
                beneficiary.name, diary_summaries, days, analysis_type
            )

            # Gerar análise
            analysis = await self.llm_service.chat(prompt)

            # Calcular estatísticas básicas
            stats = self._calculate_statistics(diaries)

            return Result.ok({
                "analysis": analysis,
                "beneficiary_name": beneficiary.name,
                "period": {
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "days": days,
                    "entries_count": len(diaries)
                },
                "statistics": stats,
                "analysis_type": analysis_type
            })

        except Exception as e:
            return Result.error(f"Erro ao analisar padrões comportamentais: {str(e)}")

    def _create_diary_summaries(self, diaries) -> str:
        """Cria resumos estruturados dos diários"""
        summaries = []

        for diary in diaries:
            parts = [f"Data: {diary.diary_date}"]

            if diary.behavior_rating:
                parts.append(f"Comportamento: {diary.behavior_rating}/5")
            if diary.behavior_description:
                parts.append(f"  {diary.behavior_description[:100]}")

            if diary.crisis_occurred:
                parts.append(f"⚠️ Crise: {diary.crisis_description[:100] if diary.crisis_description else 'Sim'}")

            if diary.mood_rating:
                parts.append(f"Humor: {diary.mood_rating}/5 ({diary.emotional_state or 'N/A'})")

            if diary.activity_engagement:
                parts.append(f"Engajamento: {diary.activity_engagement}/5")

            if diary.peer_interaction or diary.adult_interaction:
                parts.append(
                    f"Interação - Pares: {diary.peer_interaction or 'N/A'}/5, Adultos: {diary.adult_interaction or 'N/A'}/5"
                )

            if diary.achievements:
                parts.append(f"Conquistas: {diary.achievements[:100]}")

            summaries.append("\n".join(parts))

        return "\n\n---\n\n".join(summaries)

    def _get_analysis_prompt(
        self, beneficiary_name: str, summaries: str, days: int, analysis_type: str
    ) -> str:
        """Gera o prompt apropriado baseado no tipo de análise"""

        base_context = f"""
        Você é um especialista em análise comportamental de alunos com TEA.
        Analise os seguintes registros diários dos últimos {days} dias do aluno {beneficiary_name}.

        REGISTROS DIÁRIOS:
        {summaries}
        """

        if analysis_type == "crisis":
            return base_context + """

            FOCO DA ANÁLISE: SITUAÇÕES DE CRISE

            Por favor, analise:
            1. Frequência e padrões de crises
            2. Gatilhos identificados
            3. Efetividade das intervenções
            4. Recomendações para prevenção e manejo de crises

            Seja específico, objetivo e forneça recomendações práticas.
            """

        elif analysis_type == "progress":
            return base_context + """

            FOCO DA ANÁLISE: PROGRESSOS E CONQUISTAS

            Por favor, analise:
            1. Evolução das habilidades (comportamento, socialização, autonomia, comunicação)
            2. Conquistas e avanços observados
            3. Áreas de maior desenvolvimento
            4. Recomendações para manutenção e expansão dos progressos

            Destaque pontos positivos e oportunidades de crescimento.
            """

        else:  # comprehensive
            return base_context + """

            ANÁLISE ABRANGENTE

            Por favor, forneça uma análise detalhada incluindo:

            1. PADRÕES COMPORTAMENTAIS:
               - Tendências gerais de comportamento
               - Variações e flutuações
               - Fatores que influenciam o comportamento

            2. ESTADO EMOCIONAL:
               - Padrões de humor
               - Situações que afetam o estado emocional

            3. SOCIALIZAÇÃO:
               - Qualidade das interações
               - Progressos ou dificuldades

            4. SITUAÇÕES DE CRISE:
               - Frequência e padrões
               - Gatilhos identificados
               - Efetividade das intervenções

            5. DESEMPENHO ACADÊMICO/ATIVIDADES:
               - Níveis de engajamento
               - Áreas de interesse e dificuldade

            6. RECOMENDAÇÕES PEDAGÓGICAS:
               - Estratégias efetivas observadas
               - Sugestões de intervenções
               - Adaptações recomendadas
               - Objetivos para o PEI

            Seja específico, use dados dos registros e forneça recomendações práticas e baseadas em evidências.
            """

    def _calculate_statistics(self, diaries) -> dict:
        """Calcula estatísticas básicas dos registros"""
        stats = {
            "total_entries": len(diaries),
            "crisis_count": sum(1 for d in diaries if d.crisis_occurred),
            "average_behavior_rating": 0,
            "average_mood_rating": 0,
            "average_engagement": 0,
        }

        behavior_ratings = [d.behavior_rating for d in diaries if d.behavior_rating]
        if behavior_ratings:
            stats["average_behavior_rating"] = round(
                sum(behavior_ratings) / len(behavior_ratings), 2
            )

        mood_ratings = [d.mood_rating for d in diaries if d.mood_rating]
        if mood_ratings:
            stats["average_mood_rating"] = round(
                sum(mood_ratings) / len(mood_ratings), 2
            )

        engagement_ratings = [
            d.activity_engagement for d in diaries if d.activity_engagement
        ]
        if engagement_ratings:
            stats["average_engagement"] = round(
                sum(engagement_ratings) / len(engagement_ratings), 2
            )

        return stats

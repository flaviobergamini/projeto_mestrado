from datetime import datetime
from core.kernel.result import Result
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini
from infrastructure.repositories.diary_embedding_gemini_repository import DiaryEmbeddingGeminiRepository
from infrastructure.repositories.diary_repository import DiaryRepository
from infrastructure.services.llm_service import LLMService
import numpy as np


class GenerateDiaryEmbeddingUseCase:
    """
    Caso de uso para gerar embeddings de um registro diário usando Gemini.
    Cria um resumo estruturado do diário e gera embeddings para busca semântica.
    """

    def __init__(
        self,
        diary_repository: DiaryRepository,
        diary_embedding_gemini_repository: DiaryEmbeddingGeminiRepository,
        llm_service: LLMService,
    ):
        self.diary_repository = diary_repository
        self.diary_embedding_gemini_repository = diary_embedding_gemini_repository
        self.llm_service = llm_service

    async def execute(self, diary_id: int):
        try:
            # Buscar o diário
            diary = await self.diary_repository.get_by_id(diary_id)
            if not diary:
                return Result.not_found("Registro diário não encontrado")

            # Configurar LLM Service com Gemini
            self.llm_service.configure("gemini")

            # Criar um texto estruturado com os dados do diário
            diary_text = self._create_diary_text(diary)

            # Gerar resumo usando LLM
            prompt = f"""
            Resuma o seguinte registro diário de acompanhamento de aluno com TEA de forma clara e estruturada.
            Mantenha todos os aspectos importantes: comportamento, atividades, socialização, crises, estado emocional, comunicação e autonomia.
            Seja conciso mas não perca informações relevantes.

            Registro diário:
            {diary_text}

            Resumo estruturado:
            """

            summary = await self.llm_service.chat(prompt)

            # Dividir em chunks se necessário
            chunks = self.llm_service.split_text(summary)

            # Gerar embeddings para cada chunk
            for chunk in chunks:
                embedding = await self.llm_service.generate_embeddings(chunk)

                if len(embedding) == 768:
                    if isinstance(embedding, list):
                        embedding = np.array(embedding)

                    diary_embedding = DiaryEmbeddingGemini(
                        diary_id=diary.id,
                        beneficiary_id=diary.beneficiary_id,
                        content=chunk,
                        meta_data={
                            "diary_date": str(diary.diary_date),
                            "user_id": diary.user_id,
                            "crisis_occurred": diary.crisis_occurred,
                            "behavior_rating": diary.behavior_rating,
                            "mood_rating": diary.mood_rating,
                        },
                        embedding=embedding,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow(),
                    )

                    await self.diary_embedding_gemini_repository.add(diary_embedding)

            return Result.ok(
                {"message": "Embeddings gerados com sucesso", "diary_id": diary_id}
            )
        except Exception as e:
            return Result.error(f"Erro ao gerar embeddings: {str(e)}")

    def _create_diary_text(self, diary) -> str:
        """Cria um texto estruturado com os dados do diário"""
        sections = []

        sections.append(f"Data: {diary.diary_date}")

        if diary.behavior_description:
            sections.append(
                f"Comportamento (avaliação {diary.behavior_rating}/5): {diary.behavior_description}"
            )

        if diary.activity_performance:
            sections.append(
                f"Desempenho em atividades (engajamento {diary.activity_engagement}/5): {diary.activity_performance}"
            )

        if diary.completed_activities:
            sections.append(f"Atividades completadas: {diary.completed_activities}")

        if diary.socialization_description:
            sections.append(
                f"Socialização (interação com pares {diary.peer_interaction}/5, adultos {diary.adult_interaction}/5): {diary.socialization_description}"
            )

        if diary.crisis_occurred:
            crisis_text = f"Crise ocorrida (duração: {diary.crisis_duration_minutes} minutos)"
            if diary.crisis_description:
                crisis_text += f"\nDescrição: {diary.crisis_description}"
            if diary.crisis_trigger:
                crisis_text += f"\nGatilho: {diary.crisis_trigger}"
            if diary.crisis_intervention:
                crisis_text += f"\nIntervenção: {diary.crisis_intervention}"
            sections.append(crisis_text)

        if diary.emotional_state:
            sections.append(
                f"Estado emocional: {diary.emotional_state} (humor {diary.mood_rating}/5)"
            )

        if diary.communication_description:
            sections.append(
                f"Comunicação (verbal {diary.verbal_communication}/5, não-verbal {diary.non_verbal_communication}/5): {diary.communication_description}"
            )

        if diary.autonomy_description:
            sections.append(
                f"Autonomia (autocuidado {diary.self_care_skills}/5, independência {diary.task_independence}/5): {diary.autonomy_description}"
            )

        if diary.achievements:
            sections.append(f"Conquistas: {diary.achievements}")

        if diary.general_observations:
            sections.append(f"Observações gerais: {diary.general_observations}")

        if diary.teacher_suggestions:
            sections.append(f"Sugestões do professor: {diary.teacher_suggestions}")

        if diary.adaptations_needed:
            sections.append(f"Adaptações necessárias: {diary.adaptations_needed}")

        return "\n\n".join(sections)

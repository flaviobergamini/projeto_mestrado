from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from datetime import datetime
from core.kernel.container import Container
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.create_diary_use_case import CreateDiaryUseCase
from core.use_case.list_diary_use_case import ListDiaryUseCase
from core.use_case.get_diary_by_id_use_case import GetDiaryByIdUseCase
from core.use_case.get_diary_by_beneficiary_use_case import GetDiaryByBeneficiaryUseCase
from core.use_case.update_diary_use_case import UpdateDiaryUseCase
from core.use_case.delete_diary_use_case import DeleteDiaryUseCase
from core.use_case.generate_diary_embedding_use_case import GenerateDiaryEmbeddingUseCase
from core.use_case.query_diary_rag_use_case import QueryDiaryRAGUseCase
from core.use_case.analyze_behavior_patterns_use_case import AnalyzeBehaviorPatternsUseCase
from domain.schema import (
    DiaryEmbeddingRequest,
    DiaryCreateRequest,
    DiaryUpdateRequest,
    DiaryResponse,
    DiaryQueryRAGRequest,
    BehaviorAnalysisRequest,
    GenerateEmbeddingRequest
)
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from infrastructure.models.diary import Diary

router = APIRouter(prefix="/diary", tags=["Diary"])


# ==================== ROTAS CRUD DO DIÁRIO ====================

@router.post("/create-entry")
@inject
async def create_diary_entry(
    request: DiaryCreateRequest,
    use_case: CreateDiaryUseCase = Depends(
        Provide[Container.create_diary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Cria um novo registro diário de acompanhamento do aluno.
    O registro inclui informações sobre comportamento, atividades, socialização,
    crises, estado emocional, comunicação e autonomia.
    """
    try:
        diary = Diary(
            beneficiary_id=request.beneficiary_id,
            user_id=int(user_id),
            diary_date=request.diary_date,
            behavior_description=request.behavior_description,
            behavior_rating=request.behavior_rating,
            activity_performance=request.activity_performance,
            activity_engagement=request.activity_engagement,
            completed_activities=request.completed_activities,
            socialization_description=request.socialization_description,
            peer_interaction=request.peer_interaction,
            adult_interaction=request.adult_interaction,
            crisis_occurred=request.crisis_occurred,
            crisis_description=request.crisis_description,
            crisis_trigger=request.crisis_trigger,
            crisis_intervention=request.crisis_intervention,
            crisis_duration_minutes=request.crisis_duration_minutes,
            emotional_state=request.emotional_state,
            mood_rating=request.mood_rating,
            communication_description=request.communication_description,
            verbal_communication=request.verbal_communication,
            non_verbal_communication=request.non_verbal_communication,
            autonomy_description=request.autonomy_description,
            self_care_skills=request.self_care_skills,
            task_independence=request.task_independence,
            general_observations=request.general_observations,
            teacher_suggestions=request.teacher_suggestions,
            adaptations_needed=request.adaptations_needed,
            achievements=request.achievements
        )

        response = await use_case.execute(diary)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        diary_response = DiaryResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            user_id=response.value.user_id,
            diary_date=str(response.value.diary_date),
            behavior_description=response.value.behavior_description,
            behavior_rating=response.value.behavior_rating,
            activity_performance=response.value.activity_performance,
            activity_engagement=response.value.activity_engagement,
            completed_activities=response.value.completed_activities,
            socialization_description=response.value.socialization_description,
            peer_interaction=response.value.peer_interaction,
            adult_interaction=response.value.adult_interaction,
            crisis_occurred=response.value.crisis_occurred,
            crisis_description=response.value.crisis_description,
            crisis_trigger=response.value.crisis_trigger,
            crisis_intervention=response.value.crisis_intervention,
            crisis_duration_minutes=response.value.crisis_duration_minutes,
            emotional_state=response.value.emotional_state,
            mood_rating=response.value.mood_rating,
            communication_description=response.value.communication_description,
            verbal_communication=response.value.verbal_communication,
            non_verbal_communication=response.value.non_verbal_communication,
            autonomy_description=response.value.autonomy_description,
            self_care_skills=response.value.self_care_skills,
            task_independence=response.value.task_independence,
            general_observations=response.value.general_observations,
            teacher_suggestions=response.value.teacher_suggestions,
            adaptations_needed=response.value.adaptations_needed,
            achievements=response.value.achievements,
            created_at=str(response.value.created_at),
            updated_at=str(response.value.updated_at)
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": diary_response.dict()})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.get("/list")
@inject
async def list_diaries(
    use_case: ListDiaryUseCase = Depends(
        Provide[Container.list_diary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Lista todos os registros diários do sistema.
    """
    try:
        response = await use_case.execute()

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        diaries = [
            DiaryResponse(
                id=d.id,
                beneficiary_id=d.beneficiary_id,
                user_id=d.user_id,
                diary_date=str(d.diary_date),
                behavior_description=d.behavior_description,
                behavior_rating=d.behavior_rating,
                activity_performance=d.activity_performance,
                activity_engagement=d.activity_engagement,
                completed_activities=d.completed_activities,
                socialization_description=d.socialization_description,
                peer_interaction=d.peer_interaction,
                adult_interaction=d.adult_interaction,
                crisis_occurred=d.crisis_occurred,
                crisis_description=d.crisis_description,
                crisis_trigger=d.crisis_trigger,
                crisis_intervention=d.crisis_intervention,
                crisis_duration_minutes=d.crisis_duration_minutes,
                emotional_state=d.emotional_state,
                mood_rating=d.mood_rating,
                communication_description=d.communication_description,
                verbal_communication=d.verbal_communication,
                non_verbal_communication=d.non_verbal_communication,
                autonomy_description=d.autonomy_description,
                self_care_skills=d.self_care_skills,
                task_independence=d.task_independence,
                general_observations=d.general_observations,
                teacher_suggestions=d.teacher_suggestions,
                adaptations_needed=d.adaptations_needed,
                achievements=d.achievements,
                created_at=str(d.created_at),
                updated_at=str(d.updated_at)
            ) for d in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [d.dict() for d in diaries]})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.get("/{diary_id}")
@inject
async def get_diary_by_id(
    diary_id: int,
    use_case: GetDiaryByIdUseCase = Depends(
        Provide[Container.get_diary_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Busca um registro diário específico por ID.
    """
    try:
        response = await use_case.execute(diary_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        diary_response = DiaryResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            user_id=response.value.user_id,
            diary_date=str(response.value.diary_date),
            behavior_description=response.value.behavior_description,
            behavior_rating=response.value.behavior_rating,
            activity_performance=response.value.activity_performance,
            activity_engagement=response.value.activity_engagement,
            completed_activities=response.value.completed_activities,
            socialization_description=response.value.socialization_description,
            peer_interaction=response.value.peer_interaction,
            adult_interaction=response.value.adult_interaction,
            crisis_occurred=response.value.crisis_occurred,
            crisis_description=response.value.crisis_description,
            crisis_trigger=response.value.crisis_trigger,
            crisis_intervention=response.value.crisis_intervention,
            crisis_duration_minutes=response.value.crisis_duration_minutes,
            emotional_state=response.value.emotional_state,
            mood_rating=response.value.mood_rating,
            communication_description=response.value.communication_description,
            verbal_communication=response.value.verbal_communication,
            non_verbal_communication=response.value.non_verbal_communication,
            autonomy_description=response.value.autonomy_description,
            self_care_skills=response.value.self_care_skills,
            task_independence=response.value.task_independence,
            general_observations=response.value.general_observations,
            teacher_suggestions=response.value.teacher_suggestions,
            adaptations_needed=response.value.adaptations_needed,
            achievements=response.value.achievements,
            created_at=str(response.value.created_at),
            updated_at=str(response.value.updated_at)
        )

        return JSONResponse(status_code=200, content={"data": diary_response.dict()})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.get("/beneficiary/{beneficiary_id}")
@inject
async def get_diaries_by_beneficiary(
    beneficiary_id: int,
    use_case: GetDiaryByBeneficiaryUseCase = Depends(
        Provide[Container.get_diary_by_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Lista todos os registros diários de um beneficiário específico.
    Útil para análise de padrões comportamentais ao longo do tempo.
    """
    try:
        response = await use_case.execute(beneficiary_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        diaries = [
            DiaryResponse(
                id=d.id,
                beneficiary_id=d.beneficiary_id,
                user_id=d.user_id,
                diary_date=str(d.diary_date),
                behavior_description=d.behavior_description,
                behavior_rating=d.behavior_rating,
                activity_performance=d.activity_performance,
                activity_engagement=d.activity_engagement,
                completed_activities=d.completed_activities,
                socialization_description=d.socialization_description,
                peer_interaction=d.peer_interaction,
                adult_interaction=d.adult_interaction,
                crisis_occurred=d.crisis_occurred,
                crisis_description=d.crisis_description,
                crisis_trigger=d.crisis_trigger,
                crisis_intervention=d.crisis_intervention,
                crisis_duration_minutes=d.crisis_duration_minutes,
                emotional_state=d.emotional_state,
                mood_rating=d.mood_rating,
                communication_description=d.communication_description,
                verbal_communication=d.verbal_communication,
                non_verbal_communication=d.non_verbal_communication,
                autonomy_description=d.autonomy_description,
                self_care_skills=d.self_care_skills,
                task_independence=d.task_independence,
                general_observations=d.general_observations,
                teacher_suggestions=d.teacher_suggestions,
                adaptations_needed=d.adaptations_needed,
                achievements=d.achievements,
                created_at=str(d.created_at),
                updated_at=str(d.updated_at)
            ) for d in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [d.dict() for d in diaries]})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.put("/update/{diary_id}")
@inject
async def update_diary(
    diary_id: int,
    request: DiaryUpdateRequest,
    use_case: UpdateDiaryUseCase = Depends(
        Provide[Container.update_diary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Atualiza um registro diário existente.
    """
    try:
        # Construir dict apenas com campos não-None
        update_data = {k: v for k, v in request.dict().items() if v is not None}

        response = await use_case.execute(diary_id, **update_data)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        diary_response = DiaryResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            user_id=response.value.user_id,
            diary_date=str(response.value.diary_date),
            behavior_description=response.value.behavior_description,
            behavior_rating=response.value.behavior_rating,
            activity_performance=response.value.activity_performance,
            activity_engagement=response.value.activity_engagement,
            completed_activities=response.value.completed_activities,
            socialization_description=response.value.socialization_description,
            peer_interaction=response.value.peer_interaction,
            adult_interaction=response.value.adult_interaction,
            crisis_occurred=response.value.crisis_occurred,
            crisis_description=response.value.crisis_description,
            crisis_trigger=response.value.crisis_trigger,
            crisis_intervention=response.value.crisis_intervention,
            crisis_duration_minutes=response.value.crisis_duration_minutes,
            emotional_state=response.value.emotional_state,
            mood_rating=response.value.mood_rating,
            communication_description=response.value.communication_description,
            verbal_communication=response.value.verbal_communication,
            non_verbal_communication=response.value.non_verbal_communication,
            autonomy_description=response.value.autonomy_description,
            self_care_skills=response.value.self_care_skills,
            task_independence=response.value.task_independence,
            general_observations=response.value.general_observations,
            teacher_suggestions=response.value.teacher_suggestions,
            adaptations_needed=response.value.adaptations_needed,
            achievements=response.value.achievements,
            created_at=str(response.value.created_at),
            updated_at=str(response.value.updated_at)
        )

        return JSONResponse(status_code=200, content={"data": diary_response.dict()})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.delete("/delete/{diary_id}")
@inject
async def delete_diary(
    diary_id: int,
    use_case: DeleteDiaryUseCase = Depends(
        Provide[Container.delete_diary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Deleta um registro diário.
    """
    try:
        response = await use_case.execute(diary_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Registro diário deletado com sucesso"})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


# ==================== ROTAS RAG E ANÁLISE INTELIGENTE ====================

@router.post("/generate-embedding/{diary_id}")
@inject
async def generate_diary_embedding(
    diary_id: int,
    use_case: GenerateDiaryEmbeddingUseCase = Depends(
        Provide[Container.generate_diary_embedding_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Gera embeddings para um registro diário específico usando Gemini.
    Útil para regenerar embeddings ou para diários criados antes da implementação do RAG.
    """
    try:
        response = await use_case.execute(diary_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": response.value})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.post("/query-rag")
@inject
async def query_diary_rag(
    request: DiaryQueryRAGRequest,
    use_case: QueryDiaryRAGUseCase = Depends(
        Provide[Container.query_diary_rag_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Realiza consultas sobre os registros diários usando RAG (Retrieval Augmented Generation).
    Permite fazer perguntas sobre o histórico de um beneficiário específico.

    Exemplos de perguntas:
    - "Como foi o comportamento do aluno na última semana?"
    - "Quais foram os principais gatilhos de crises identificados?"
    - "Houve evolução na socialização com os colegas?"
    - "Quais atividades o aluno mais se engajou?"
    """
    try:
        response = await use_case.execute(
            request.beneficiary_id,
            request.query,
            request.limit
        )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": response.value})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


@router.post("/analyze-behavior")
@inject
async def analyze_behavior_patterns(
    request: BehaviorAnalysisRequest,
    use_case: AnalyzeBehaviorPatternsUseCase = Depends(
        Provide[Container.analyze_behavior_patterns_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Analisa padrões comportamentais de um beneficiário usando IA.

    Tipos de análise disponíveis:
    - "comprehensive": Análise abrangente de todos os aspectos
    - "crisis": Foco em situações de crise e gatilhos
    - "progress": Foco em progressos e conquistas

    Retorna uma análise detalhada com:
    - Padrões comportamentais identificados
    - Tendências emocionais
    - Recomendações pedagógicas
    - Sugestões para o PEI
    - Estatísticas do período analisado
    """
    try:
        response = await use_case.execute(
            request.beneficiary_id,
            request.days,
            request.analysis_type
        )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": response.value})
    except Exception as e:
        return JSONResponse(content={"error": f"Internal server error: {str(e)}"}, status_code=500)


# ==================== ROTA ANTIGA DE EMBEDDING (Mantida para compatibilidade) ====================

@router.post("/create-embedding")
@inject
async def create_embedding(
    request: DiaryEmbeddingRequest,
    use_case: DiaryEmbeddingUseCase = Depends(
        Provide[Container.diary_embedding_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Rota antiga para geração de embeddings de texto do diário.
    Mantida para compatibilidade com código existente.
    """
    try:
        response = await use_case.execute(request.diary, request.model, request.beneficiary_id, user_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_201_CREATED, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
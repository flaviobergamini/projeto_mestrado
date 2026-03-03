from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.diary_conceptual_use_case import DiaryConceptualUseCase
from core.use_case.generate_diary_embedding_use_case import GenerateDiaryEmbeddingUseCase
from core.use_case.query_diary_rag_use_case import QueryDiaryRAGUseCase
from core.use_case.analyze_behavior_patterns_use_case import AnalyzeBehaviorPatternsUseCase
from infrastructure.services.storage_service import StorageService
from domain.schema import (
    DiaryConceptualRequest,
    DiaryQueryRAGRequest,
    BehaviorAnalysisRequest,
)
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
import json

from infrastructure.models.diary_conceptual import DiaryConceptual

router = APIRouter(prefix="/diary", tags=["Diary"])


# ==================== ROTA DE CRIAÇÃO DO DIÁRIO ====================

@router.post("/create")
@inject
async def create_diary(
    request: DiaryConceptualRequest,
    use_case: DiaryConceptualUseCase = Depends(
        Provide[Container.diary_conceptual_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    """
    Cria um novo registro diário conceitual (texto único).
    O registro é processado via RAG no momento da criação.
    """
    try:
        diary = DiaryConceptual(**request.model_dump())

        response = await use_case.execute(diary, user_id)

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
    except Exception as e:
        print(e)
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)


@router.get("/questions")
@inject
async def get_diary_questions(
    storage_service: StorageService = Depends(Provide[Container.storage_service])
):
    """
    Retorna o JSON com as perguntas padrão para cadastro de diário.
    O usuário pode usar esse template e customizá-lo conforme necessário.
    O template é buscado do Supabase Storage.
    """
    try:
        # Caminho padrão do template no storage
        template_path = "templates/diary_questions.json"

        # Buscar arquivo do storage
        file_content = storage_service.download_file(template_path)
        questions_template = json.loads(file_content.decode('utf-8'))

        return JSONResponse(
            status_code=HTTP_200_OK,
            content=questions_template
        )
    except Exception as e:
        print(f"Erro ao buscar template: {str(e)}")
        return JSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content={"error": "Template de perguntas não encontrado no storage"}
        )


# ==================== ROTAS RAG E ANÁLISE INTELIGENTE ====================

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

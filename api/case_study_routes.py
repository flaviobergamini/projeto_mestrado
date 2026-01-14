from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.study_case_use_case import StudyCaseUseCase
from infrastructure.services.storage_service import StorageService
from domain.schema import StudyCaseRequest
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK
from dependency_injector.wiring import inject, Provide
import json

from infrastructure.models.study_case import StudyCase

router = APIRouter(prefix="/case-study", tags=["CaseStudy"])


@router.post("/create")
@inject
async def create_case_study(
    request: StudyCaseRequest,
    use_case: StudyCaseUseCase = Depends(
        Provide[Container.study_case_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        study_case = StudyCase(**request.model_dump())

        response = await use_case.execute(study_case, user_id)

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
async def get_case_study_questions(
    storage_service: StorageService = Depends(Provide[Container.storage_service])
):
    """
    Retorna o JSON com as perguntas padrão para estudo de caso.
    O usuário pode usar esse template e customizá-lo conforme necessário.
    O template é buscado do Supabase Storage.
    """
    try:
        # Caminho padrão do template no storage
        template_path = "templates/case_study_questions.json"

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

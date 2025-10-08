from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from domain.schema import DiaryRequest
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

router = APIRouter(prefix="/diary", tags=["Diary"])


@router.post("/create")
@inject
async def create(
    request: DiaryRequest, 
    use_case: DiaryEmbeddingUseCase = Depends(
        Provide[Container.diary_embedding_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
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
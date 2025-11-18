from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.institution_use_case import InstitutionUseCase
from domain.schema import InstitutionStudyCaseRequest
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR
from dependency_injector.wiring import inject, Provide

from infrastructure.models.institution import Institution

router = APIRouter(prefix="/institution", tags=["Institution"])


@router.post("/create")
@inject
async def create_institution(
    request: InstitutionStudyCaseRequest,
    use_case: InstitutionUseCase = Depends(
        Provide[Container.institution_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        institution = Institution(**request.model_dump())

        response = await use_case.execute(institution, user_id)

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

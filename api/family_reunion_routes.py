from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_family_reunion_use_case import CreateFamilyReunionUseCase
from core.use_case.delete_family_reunion_use_case import DeleteFamilyReunionUseCase
from core.use_case.get_family_reunion_by_id_use_case import GetFamilyReunionByIdUseCase
from core.use_case.list_family_reunion_use_case import ListFamilyReunionUseCase
from core.use_case.update_family_reunion_use_case import UpdateFamilyReunionUseCase
from domain.schema import FamilyReunionRequest, FamilyReunionResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.family_reunion import FamilyReunion

router = APIRouter(prefix="/family-reunion", tags=["FamilyReunion"], dependencies=[Depends(require_roles("admin", "school_admin"))])


@router.post("/create")
@inject
async def create(
    request: FamilyReunionRequest,
    use_case: CreateFamilyReunionUseCase = Depends(
        Provide[Container.create_family_reunion_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        family_reunion = FamilyReunion(
            beneficiary_id=request.beneficiary_id,
            supervisor_id=request.supervisor_id,
            reunion_date=request.reunion_date,
            description=request.description,
            family_feedback=request.family_feedback
        )
        response = await use_case.execute(family_reunion)

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

        response_family_reunion = FamilyReunionResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            reunion_date=str(response.value.reunion_date),
            description=response.value.description,
            family_feedback=response.value.family_feedback
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_family_reunion.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListFamilyReunionUseCase = Depends(
        Provide[Container.list_family_reunion_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute()

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        family_reunions = [
            FamilyReunionResponse(
                id=fr.id,
                beneficiary_id=fr.beneficiary_id,
                supervisor_id=fr.supervisor_id,
                reunion_date=str(fr.reunion_date),
                description=fr.description,
                family_feedback=fr.family_feedback
            ) for fr in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [fr.dict() for fr in family_reunions]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{family_reunion_id}")
@inject
async def get_family_reunion_by_id(
    family_reunion_id: int,
    use_case: GetFamilyReunionByIdUseCase = Depends(
        Provide[Container.get_family_reunion_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(family_reunion_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Reunião familiar não encontrada"}
            )

        response_family_reunion = FamilyReunionResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            reunion_date=str(response.value.reunion_date),
            description=response.value.description,
            family_feedback=response.value.family_feedback
        )

        return JSONResponse(status_code=200, content={"data": response_family_reunion.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{family_reunion_id}")
@inject
async def update(
    family_reunion_id: int,
    request: FamilyReunionRequest,
    use_case: UpdateFamilyReunionUseCase = Depends(
        Provide[Container.update_family_reunion_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        family_reunion = FamilyReunion(
            id=family_reunion_id,
            beneficiary_id=request.beneficiary_id,
            supervisor_id=request.supervisor_id,
            reunion_date=request.reunion_date,
            description=request.description,
            family_feedback=request.family_feedback
        )

        response = await use_case.execute(family_reunion)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Reunião familiar não encontrada"}
            )

        response_family_reunion = FamilyReunionResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            reunion_date=str(response.value.reunion_date),
            description=response.value.description,
            family_feedback=response.value.family_feedback
        )

        return JSONResponse(status_code=200, content={"data": response_family_reunion.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{family_reunion_id}")
@inject
async def delete(
    family_reunion_id: int,
    use_case: DeleteFamilyReunionUseCase = Depends(
        Provide[Container.delete_family_reunion_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(family_reunion_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Reunião familiar não encontrada"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Reunião familiar deletada com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

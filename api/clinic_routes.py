from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_clinic_use_case import CreateClinicUseCase
from core.use_case.delete_clinic_use_case import DeleteClinicUseCase
from core.use_case.get_clinic_by_id_use_case import GetClinicByIdUseCase
from core.use_case.list_clinic_use_case import ListClinicUseCase
from core.use_case.update_clinic_use_case import UpdateClinicUseCase
from domain.schema import ClinicRequest, ClinicResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.clinic import Clinic

router = APIRouter(prefix="/clinic", tags=["Clinic"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: ClinicRequest,
    use_case: CreateClinicUseCase = Depends(
        Provide[Container.create_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        clinic = Clinic(
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )
        response = await use_case.execute(clinic)

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

        response_clinic = ClinicResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListClinicUseCase = Depends(
        Provide[Container.list_clinic_use_case],
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

        clinics = [
            ClinicResponse(
                id=clinic.id,
                name=clinic.name,
                address=clinic.address,
                telephone=clinic.telephone,
                email=clinic.email,
                responsible=clinic.responsible
            ) for clinic in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [clinic.dict() for clinic in clinics]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{clinic_id}")
@inject
async def get_clinic_by_id(
    clinic_id: int,
    use_case: GetClinicByIdUseCase = Depends(
        Provide[Container.get_clinic_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(clinic_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Clínica não encontrada"}
            )

        response_clinic = ClinicResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=200, content={"data": response_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{clinic_id}")
@inject
async def update(
    clinic_id: int,
    request: ClinicRequest,
    use_case: UpdateClinicUseCase = Depends(
        Provide[Container.update_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        clinic = Clinic(
            id=clinic_id,
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )

        response = await use_case.execute(clinic)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Clínica não encontrada"}
            )

        response_clinic = ClinicResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=200, content={"data": response_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{clinic_id}")
@inject
async def delete(
    clinic_id: int,
    use_case: DeleteClinicUseCase = Depends(
        Provide[Container.delete_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(clinic_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Clínica não encontrada"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Clínica deletada com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

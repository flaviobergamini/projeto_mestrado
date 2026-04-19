from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_beneficiary_clinic_use_case import CreateBeneficiaryClinicUseCase
from core.use_case.delete_beneficiary_clinic_use_case import DeleteBeneficiaryClinicUseCase
from core.use_case.get_beneficiary_clinic_by_id_use_case import GetBeneficiaryClinicByIdUseCase
from core.use_case.list_beneficiary_clinic_use_case import ListBeneficiaryClinicUseCase
from core.use_case.update_beneficiary_clinic_use_case import UpdateBeneficiaryClinicUseCase
from domain.schema import BeneficiaryClinicRequest, BeneficiaryClinicResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.beneficiary_clinic import BeneficiaryClinic

router = APIRouter(prefix="/beneficiary-clinic", tags=["BeneficiaryClinic"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: BeneficiaryClinicRequest,
    use_case: CreateBeneficiaryClinicUseCase = Depends(
        Provide[Container.create_beneficiary_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        beneficiary_clinic = BeneficiaryClinic(
            beneficiary_id=request.beneficiary_id,
            clinic_id=request.clinic_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        response = await use_case.execute(beneficiary_clinic)

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

        response_beneficiary_clinic = BeneficiaryClinicResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            clinic_id=response.value.clinic_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date)
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_beneficiary_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListBeneficiaryClinicUseCase = Depends(
        Provide[Container.list_beneficiary_clinic_use_case],
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

        beneficiary_clinics = [
            BeneficiaryClinicResponse(
                id=bc.id,
                beneficiary_id=bc.beneficiary_id,
                clinic_id=bc.clinic_id,
                start_date=str(bc.start_date),
                end_date=str(bc.end_date)
            ) for bc in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [bc.dict() for bc in beneficiary_clinics]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{beneficiary_clinic_id}")
@inject
async def get_beneficiary_clinic_by_id(
    beneficiary_clinic_id: int,
    use_case: GetBeneficiaryClinicByIdUseCase = Depends(
        Provide[Container.get_beneficiary_clinic_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(beneficiary_clinic_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Relacionamento beneficiário-clínica não encontrado"}
            )

        response_beneficiary_clinic = BeneficiaryClinicResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            clinic_id=response.value.clinic_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date)
        )

        return JSONResponse(status_code=200, content={"data": response_beneficiary_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{beneficiary_clinic_id}")
@inject
async def update(
    beneficiary_clinic_id: int,
    request: BeneficiaryClinicRequest,
    use_case: UpdateBeneficiaryClinicUseCase = Depends(
        Provide[Container.update_beneficiary_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        beneficiary_clinic = BeneficiaryClinic(
            id=beneficiary_clinic_id,
            beneficiary_id=request.beneficiary_id,
            clinic_id=request.clinic_id,
            start_date=request.start_date,
            end_date=request.end_date
        )

        response = await use_case.execute(beneficiary_clinic)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Relacionamento beneficiário-clínica não encontrado"}
            )

        response_beneficiary_clinic = BeneficiaryClinicResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            clinic_id=response.value.clinic_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date)
        )

        return JSONResponse(status_code=200, content={"data": response_beneficiary_clinic.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{beneficiary_clinic_id}")
@inject
async def delete(
    beneficiary_clinic_id: int,
    use_case: DeleteBeneficiaryClinicUseCase = Depends(
        Provide[Container.delete_beneficiary_clinic_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(beneficiary_clinic_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Relacionamento beneficiário-clínica não encontrado"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Relacionamento beneficiário-clínica deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

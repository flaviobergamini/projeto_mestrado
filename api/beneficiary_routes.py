from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.create_beneficiary_use_case import CreateBeneficiaryUseCase
from core.use_case.delete_school_use_case import DeleteSchoolUseCase
from core.use_case.diary_embedding_use_case import DiaryEmbeddingUseCase
from core.use_case.get_beneficiary_use_case import GetBeneficiaryByIdUseCase
from core.use_case.list_beneficiary_use_case import ListBeneficiaryUseCase
from core.use_case.update_beneficiary_use_case import UpdateBeneficiaryUseCase
from domain.schema import BeneficiaryRequest, BeneficiaryResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.beneficiary import Beneficiary

router = APIRouter(prefix="/beneficiary", tags=["Beneficiary"])


@router.post("/create")
@inject
async def create(
    request: BeneficiaryRequest, 
    use_case: CreateBeneficiaryUseCase = Depends(
        Provide[Container.create_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        beneficiary = Beneficiary(
            name=request.name,
            date_of_birth=request.date_of_birth,
            diagnosis=request.diagnosis,
            main_responsible=request.main_responsible,
            responsible_contact=request.responsible_contact,
            entry_date=request.entry_date,
            exit_date=request.exit_date,
            status=request.status,
            school_id=request.school_id,
            healthplan_id=request.healthplan_id
        )

        response = await use_case.execute(beneficiary)

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
        
        response_beneficiary = BeneficiaryResponse(
            id=response.value.id,
            name=response.value.name,
            date_of_birth=f'{response.value.date_of_birth}',
            diagnosis=response.value.diagnosis,
            main_responsible=response.value.main_responsible,
            responsible_contact=response.value.responsible_contact,
            entry_date=f'{response.value.entry_date}',
            exit_date=f'{response.value.exit_date}',
            status=response.value.status,
            school_id=response.value.school_id,
            healthplan_id=response.value.healthplan_id,
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_beneficiary.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.get("/list")
@inject
async def list(
    use_case: ListBeneficiaryUseCase = Depends(
        Provide[Container.list_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute()
        
        beneficiaries_response = [
            BeneficiaryResponse(
                id=beneficiary.id,
                name=beneficiary.name,
                date_of_birth=f'{beneficiary.date_of_birth}',
                diagnosis=beneficiary.diagnosis,
                main_responsible=beneficiary.main_responsible,
                responsible_contact=beneficiary.responsible_contact,
                entry_date=f'{beneficiary.entry_date}',
                exit_date=f'{beneficiary.exit_date}',
                status=beneficiary.status,
                school_id=beneficiary.school_id,
                healthplan_id=beneficiary.healthplan_id,
            ) for beneficiary in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [b.dict() for b in beneficiaries_response]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{beneficiary_id}")
@inject
async def get_by_id(
    beneficiary_id: int,
    use_case: GetBeneficiaryByIdUseCase = Depends(
        Provide[Container.get_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
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
        
        beneficiary = response.value
        beneficiary_response = BeneficiaryResponse(
            id=beneficiary.id,
            name=beneficiary.name,
            date_of_birth=f'{beneficiary.date_of_birth}',
            diagnosis=beneficiary.diagnosis,
            main_responsible=beneficiary.main_responsible,
            responsible_contact=beneficiary.responsible_contact,
            entry_date=f'{beneficiary.entry_date}',
            exit_date=f'{beneficiary.exit_date}',
            status=beneficiary.status,
            school_id=beneficiary.school_id,
            healthplan_id=beneficiary.healthplan_id,
        )

        return JSONResponse(status_code=200, content={"data": beneficiary_response.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{beneficiary_id}")
@inject
async def update(
    beneficiary_id: int,
    request: BeneficiaryRequest, 
    use_case: UpdateBeneficiaryUseCase = Depends(
        Provide[Container.update_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        beneficiary = Beneficiary (
            id = beneficiary_id,
            name = request.name,
            date_of_birth = request.date_of_birth, 
            diagnosis = request.diagnosis,
            main_responsible = request.main_responsible,
            responsible_contact = request.responsible_contact,
            entry_date = request.entry_date,
            exit_date = request.exit_date,
            status = request.status,
            school_id = request.school_id,
            healthplan_id = request.healthplan_id
        )

        response = await use_case.execute(beneficiary)
        
        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )
        
        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error":  response.not_found_error}
            )
        
        beneficiary = response.value
        beneficiary_response = BeneficiaryResponse(
            id=beneficiary.id,
            name=beneficiary.name,
            date_of_birth=f'{beneficiary.date_of_birth}',
            diagnosis=beneficiary.diagnosis,
            main_responsible=beneficiary.main_responsible,
            responsible_contact=beneficiary.responsible_contact,
            entry_date=f'{beneficiary.entry_date}',
            exit_date=f'{beneficiary.exit_date}',
            status=beneficiary.status,
            school_id=beneficiary.school_id,
            healthplan_id=beneficiary.healthplan_id,
        )

        return JSONResponse(status_code=200, content={"data": beneficiary_response.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.delete("/delete/{beneficiary_id}")
@inject
async def delete(
    beneficiary_id: int,
    use_case:   DeleteSchoolUseCase = Depends(
        Provide[Container.delete_beneficiary_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
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

        return JSONResponse(status_code=200, content={"data": "Beneficiário deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
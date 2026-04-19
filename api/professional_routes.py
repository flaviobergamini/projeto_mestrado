from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_professional_use_case import CreateProfessionalUseCase
from core.use_case.delete_professional_use_case import DeleteProfessionalUseCase
from core.use_case.get_professional_by_id_use_case import GetProfessionalByIdUseCase
from core.use_case.list_professional_use_case import ListProfessionalUseCase
from core.use_case.update_professional_use_case import UpdateProfessionalUseCase
from domain.schema import ProfessionalRequest, ProfessionalResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.professional import Professional

router = APIRouter(prefix="/professional", tags=["Professional"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: ProfessionalRequest,
    use_case: CreateProfessionalUseCase = Depends(
        Provide[Container.create_professional_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        professional = Professional(
            name=request.name,
            function=request.function,
            specialty=request.specialty,
            contact=request.contact,
            availability=request.availability,
            clinic_id=request.clinic_id,
            email=request.email,
            password=request.password
        )
        response = await use_case.execute(professional)

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

        response_professional = ProfessionalResponse(
            id=response.value.id,
            name=response.value.name,
            function=response.value.function,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            clinic_id=response.value.clinic_id,
            email=response.value.email
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_professional.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListProfessionalUseCase = Depends(
        Provide[Container.list_professional_use_case],
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

        professionals = [
            ProfessionalResponse(
                id=professional.id,
                name=professional.name,
                function=professional.function,
                specialty=professional.specialty,
                contact=professional.contact,
                availability=professional.availability,
                clinic_id=professional.clinic_id,
                email=professional.email
            ) for professional in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [professional.dict() for professional in professionals]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{professional_id}")
@inject
async def get_professional_by_id(
    professional_id: int,
    use_case: GetProfessionalByIdUseCase = Depends(
        Provide[Container.get_professional_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(professional_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Profissional não encontrado"}
            )

        response_professional = ProfessionalResponse(
            id=response.value.id,
            name=response.value.name,
            function=response.value.function,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            clinic_id=response.value.clinic_id,
            email=response.value.email
        )

        return JSONResponse(status_code=200, content={"data": response_professional.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{professional_id}")
@inject
async def update(
    professional_id: int,
    request: ProfessionalRequest,
    use_case: UpdateProfessionalUseCase = Depends(
        Provide[Container.update_professional_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        professional = Professional(
            id=professional_id,
            name=request.name,
            function=request.function,
            specialty=request.specialty,
            contact=request.contact,
            availability=request.availability,
            clinic_id=request.clinic_id,
            email=request.email,
            password=request.password
        )

        response = await use_case.execute(professional)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Profissional não encontrado"}
            )

        response_professional = ProfessionalResponse(
            id=response.value.id,
            name=response.value.name,
            function=response.value.function,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            clinic_id=response.value.clinic_id,
            email=response.value.email
        )

        return JSONResponse(status_code=200, content={"data": response_professional.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{professional_id}")
@inject
async def delete(
    professional_id: int,
    use_case: DeleteProfessionalUseCase = Depends(
        Provide[Container.delete_professional_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(professional_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Profissional não encontrado"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Profissional deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

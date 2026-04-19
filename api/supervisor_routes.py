from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_supervisor_use_case import CreateSupervisorUseCase
from core.use_case.delete_supervisor_use_case import DeleteSupervisorUseCase
from core.use_case.get_supervisor_by_id_use_case import GetSupervisorByIdUseCase
from core.use_case.list_supervisor_use_case import ListSupervisorUseCase
from core.use_case.update_supervisor_use_case import UpdateSupervisorUseCase
from domain.schema import SupervisorRequest, SupervisorResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.supervisor import Supervisor

router = APIRouter(prefix="/supervisor", tags=["Supervisor"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: SupervisorRequest,
    use_case: CreateSupervisorUseCase = Depends(
        Provide[Container.create_supervisor_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        supervisor = Supervisor(
            name=request.name,
            specialty=request.specialty,
            contact=request.contact,
            availability=request.availability,
            autismia_id=request.autismia_id,
            email=request.email,
            password=request.password
        )
        response = await use_case.execute(supervisor)

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

        response_supervisor = SupervisorResponse(
            id=response.value.id,
            name=response.value.name,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            autismia_id=response.value.autismia_id,
            email=response.value.email
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_supervisor.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListSupervisorUseCase = Depends(
        Provide[Container.list_supervisor_use_case],
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

        supervisors = [
            SupervisorResponse(
                id=supervisor.id,
                name=supervisor.name,
                specialty=supervisor.specialty,
                contact=supervisor.contact,
                availability=supervisor.availability,
                autismia_id=supervisor.autismia_id,
                email=supervisor.email
            ) for supervisor in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [supervisor.dict() for supervisor in supervisors]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{supervisor_id}")
@inject
async def get_supervisor_by_id(
    supervisor_id: int,
    use_case: GetSupervisorByIdUseCase = Depends(
        Provide[Container.get_supervisor_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(supervisor_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Supervisor não encontrado"}
            )

        response_supervisor = SupervisorResponse(
            id=response.value.id,
            name=response.value.name,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            autismia_id=response.value.autismia_id,
            email=response.value.email
        )

        return JSONResponse(status_code=200, content={"data": response_supervisor.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{supervisor_id}")
@inject
async def update(
    supervisor_id: int,
    request: SupervisorRequest,
    use_case: UpdateSupervisorUseCase = Depends(
        Provide[Container.update_supervisor_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        supervisor = Supervisor(
            id=supervisor_id,
            name=request.name,
            specialty=request.specialty,
            contact=request.contact,
            availability=request.availability,
            autismia_id=request.autismia_id,
            email=request.email,
            password=request.password
        )

        response = await use_case.execute(supervisor)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Supervisor não encontrado"}
            )

        response_supervisor = SupervisorResponse(
            id=response.value.id,
            name=response.value.name,
            specialty=response.value.specialty,
            contact=response.value.contact,
            availability=response.value.availability,
            autismia_id=response.value.autismia_id,
            email=response.value.email
        )

        return JSONResponse(status_code=200, content={"data": response_supervisor.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{supervisor_id}")
@inject
async def delete(
    supervisor_id: int,
    use_case: DeleteSupervisorUseCase = Depends(
        Provide[Container.delete_supervisor_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(supervisor_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Supervisor não encontrado"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Supervisor deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

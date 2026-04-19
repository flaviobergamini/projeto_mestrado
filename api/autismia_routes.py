from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_autismia_use_case import CreateAutismiaUseCase
from core.use_case.delete_autismia_use_case import DeleteAutismiaUseCase
from core.use_case.get_autismia_by_id_use_case import GetAutismiaByIdUseCase
from core.use_case.list_autismia_use_case import ListAutismiaUseCase
from core.use_case.update_autismia_use_case import UpdateAutismiaUseCase
from domain.schema import AutismiaRequest, AutismiaResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.autismia import Autismia

router = APIRouter(prefix="/autismia", tags=["Autismia"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: AutismiaRequest,
    use_case: CreateAutismiaUseCase = Depends(
        Provide[Container.create_autismia_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        autismia = Autismia(
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )
        response = await use_case.execute(autismia)

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

        response_autismia = AutismiaResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_autismia.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListAutismiaUseCase = Depends(
        Provide[Container.list_autismia_use_case],
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

        autismias = [
            AutismiaResponse(
                id=autismia.id,
                name=autismia.name,
                address=autismia.address,
                telephone=autismia.telephone,
                email=autismia.email,
                responsible=autismia.responsible
            ) for autismia in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [autismia.dict() for autismia in autismias]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{autismia_id}")
@inject
async def get_autismia_by_id(
    autismia_id: int,
    use_case: GetAutismiaByIdUseCase = Depends(
        Provide[Container.get_autismia_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(autismia_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Autismia não encontrada"}
            )

        response_autismia = AutismiaResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=200, content={"data": response_autismia.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{autismia_id}")
@inject
async def update(
    autismia_id: int,
    request: AutismiaRequest,
    use_case: UpdateAutismiaUseCase = Depends(
        Provide[Container.update_autismia_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        autismia = Autismia(
            id=autismia_id,
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )

        response = await use_case.execute(autismia)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Autismia não encontrada"}
            )

        response_autismia = AutismiaResponse(
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=200, content={"data": response_autismia.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{autismia_id}")
@inject
async def delete(
    autismia_id: int,
    use_case: DeleteAutismiaUseCase = Depends(
        Provide[Container.delete_autismia_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(autismia_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Autismia não encontrada"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Autismia deletada com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

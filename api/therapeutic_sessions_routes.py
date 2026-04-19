from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_therapeutic_sessions_use_case import CreateTherapeuticSessionsUseCase
from core.use_case.delete_therapeutic_sessions_use_case import DeleteTherapeuticSessionsUseCase
from core.use_case.get_therapeutic_sessions_by_id_use_case import GetTherapeuticSessionsByIdUseCase
from core.use_case.list_therapeutic_sessions_use_case import ListTherapeuticSessionsUseCase
from core.use_case.update_therapeutic_sessions_use_case import UpdateTherapeuticSessionsUseCase
from domain.schema import TherapeuticSessionsRequest, TherapeuticSessionsResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.therapeutic_sessions import TherapeuticSessions

router = APIRouter(prefix="/therapeutic-sessions", tags=["TherapeuticSessions"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: TherapeuticSessionsRequest,
    use_case: CreateTherapeuticSessionsUseCase = Depends(
        Provide[Container.create_therapeutic_sessions_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        therapeutic_sessions = TherapeuticSessions(
            therapeutic_plan_id=request.therapeutic_plan_id,
            professional_id=request.professional_id,
            clinic_id=request.clinic_id,
            session_date=request.session_date,
            description=request.description,
            observation=request.observation
        )
        response = await use_case.execute(therapeutic_sessions)

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

        response_therapeutic_sessions = TherapeuticSessionsResponse(
            id=response.value.id,
            therapeutic_plan_id=response.value.therapeutic_plan_id,
            professional_id=response.value.professional_id,
            clinic_id=response.value.clinic_id,
            session_date=str(response.value.session_date),
            description=response.value.description,
            observation=response.value.observation
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_therapeutic_sessions.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListTherapeuticSessionsUseCase = Depends(
        Provide[Container.list_therapeutic_sessions_use_case],
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

        therapeutic_sessions = [
            TherapeuticSessionsResponse(
                id=ts.id,
                therapeutic_plan_id=ts.therapeutic_plan_id,
                professional_id=ts.professional_id,
                clinic_id=ts.clinic_id,
                session_date=str(ts.session_date),
                description=ts.description,
                observation=ts.observation
            ) for ts in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [ts.dict() for ts in therapeutic_sessions]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{therapeutic_sessions_id}")
@inject
async def get_therapeutic_sessions_by_id(
    therapeutic_sessions_id: int,
    use_case: GetTherapeuticSessionsByIdUseCase = Depends(
        Provide[Container.get_therapeutic_sessions_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(therapeutic_sessions_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Sessão terapêutica não encontrada"}
            )

        response_therapeutic_sessions = TherapeuticSessionsResponse(
            id=response.value.id,
            therapeutic_plan_id=response.value.therapeutic_plan_id,
            professional_id=response.value.professional_id,
            clinic_id=response.value.clinic_id,
            session_date=str(response.value.session_date),
            description=response.value.description,
            observation=response.value.observation
        )

        return JSONResponse(status_code=200, content={"data": response_therapeutic_sessions.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{therapeutic_sessions_id}")
@inject
async def update(
    therapeutic_sessions_id: int,
    request: TherapeuticSessionsRequest,
    use_case: UpdateTherapeuticSessionsUseCase = Depends(
        Provide[Container.update_therapeutic_sessions_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        therapeutic_sessions = TherapeuticSessions(
            id=therapeutic_sessions_id,
            therapeutic_plan_id=request.therapeutic_plan_id,
            professional_id=request.professional_id,
            clinic_id=request.clinic_id,
            session_date=request.session_date,
            description=request.description,
            observation=request.observation
        )

        response = await use_case.execute(therapeutic_sessions)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Sessão terapêutica não encontrada"}
            )

        response_therapeutic_sessions = TherapeuticSessionsResponse(
            id=response.value.id,
            therapeutic_plan_id=response.value.therapeutic_plan_id,
            professional_id=response.value.professional_id,
            clinic_id=response.value.clinic_id,
            session_date=str(response.value.session_date),
            description=response.value.description,
            observation=response.value.observation
        )

        return JSONResponse(status_code=200, content={"data": response_therapeutic_sessions.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{therapeutic_sessions_id}")
@inject
async def delete(
    therapeutic_sessions_id: int,
    use_case: DeleteTherapeuticSessionsUseCase = Depends(
        Provide[Container.delete_therapeutic_sessions_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(therapeutic_sessions_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Sessão terapêutica não encontrada"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Sessão terapêutica deletada com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

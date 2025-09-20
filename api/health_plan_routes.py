from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.create_health_plan_use_case import CreateHealthPlanUseCase
from core.use_case.delete_health_plan_use_case import DeleteHealthPlanUseCase
from core.use_case.get_health_plan_by_id_use_case import GetHealthPlanByIdUseCase
from core.use_case.list_health_plan_use_case import ListHealthPlanUseCase
from core.use_case.update_health_plan_use_case import UpdateHealthPlanUseCase
from domain.schema import HealthPlanRequest, HealthPlanResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.health_plan import HealthPlan

router = APIRouter(prefix="/health_plan", tags=["Health Plan"])


@router.post("/create")
@inject
async def create(
    request: HealthPlanRequest, 
    use_case: CreateHealthPlanUseCase = Depends(
        Provide[Container.create_health_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        health_plan = HealthPlan (
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            responsible=request.responsible,
            email=request.email
        )
        response = await use_case.execute(health_plan)
        
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
        
        health_plan_response = HealthPlanResponse (
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            responsible=response.value.responsible,
            email=response.value.email
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": health_plan_response.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.get("/list")
@inject
async def list(
    use_case: ListHealthPlanUseCase = Depends(
        Provide[Container.list_health_plan_use_case],
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
        
        health_plans = [
            HealthPlanResponse(
                id=hp.id,
                name=hp.name,
                address=hp.address,
                telephone=hp.telephone,
                responsible=hp.responsible,
                email=hp.email
            ) for hp in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [hp.dict() for hp in health_plans]})
    except Exception as e:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.get("/{school_id}")
@inject
async def get_health_plan_by_id(
    health_plan_id: int,
    use_case: GetHealthPlanByIdUseCase = Depends(
        Provide[Container.get_health_plan_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(health_plan_id)
        
        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )
        
        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano de saúde não encontrado"}
            )
    
        response_school = HealthPlanResponse (
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible,
            created_at=response.value.created_at,
            updated_at=response.value.updated_at,
        )

        return JSONResponse(status_code=200, content={"data": response_school.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{health_plan_id}")
@inject
async def update_health_plan(
    health_plan_id: int,
    request: HealthPlanRequest, 
    use_case: UpdateHealthPlanUseCase = Depends(
        Provide[Container.update_health_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        health_plan = HealthPlan (
            id=health_plan_id,
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )
        response = await use_case.execute(health_plan)
        
        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano de saúde não encontrado"}
            )
        
        health_plan_response = HealthPlanResponse (
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=200, content={"data": health_plan_response.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
    
@router.delete("/delete/{health_plan_id}")
@inject
async def delete_health_plan(
    health_plan_id: int,
    use_case: DeleteHealthPlanUseCase = Depends(
        Provide[Container.delete_health_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(health_plan_id)
        
        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano de saúde não encontrado"}
            )
        
        return JSONResponse(status_code=200, content={"data": "Plano de saúde deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
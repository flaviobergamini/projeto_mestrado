from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from core.use_case.create_therapeutic_plan_use_case import CreateTherapeuticPlanUseCase
from core.use_case.delete_therapeutic_plan_use_case import DeleteTherapeuticPlanUseCase
from core.use_case.get_therapeutic_plan_by_id_use_case import GetTherapeuticPlanByIdUseCase
from core.use_case.list_therapeutic_plan_use_case import ListTherapeuticPlanUseCase
from core.use_case.update_therapeutic_plan_use_case import UpdateTherapeuticPlanUseCase
from domain.schema import TherapeuticPlanRequest, TherapeuticPlanResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.therapeutic_plan import TherapeuticPlan

router = APIRouter(prefix="/therapeutic-plan", tags=["TherapeuticPlan"], dependencies=[Depends(require_roles("admin"))])


@router.post("/create")
@inject
async def create(
    request: TherapeuticPlanRequest,
    use_case: CreateTherapeuticPlanUseCase = Depends(
        Provide[Container.create_therapeutic_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        therapeutic_plan = TherapeuticPlan(
            beneficiary_id=request.beneficiary_id,
            start_date=request.start_date,
            end_date=request.end_date,
            objective=request.objective,
            description=request.description,
            workload=request.workload,
            status=request.status
        )
        response = await use_case.execute(therapeutic_plan)

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

        response_therapeutic_plan = TherapeuticPlanResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date),
            objective=response.value.objective,
            description=response.value.description,
            workload=response.value.workload,
            status=response.value.status
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_therapeutic_plan.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListTherapeuticPlanUseCase = Depends(
        Provide[Container.list_therapeutic_plan_use_case],
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

        therapeutic_plans = [
            TherapeuticPlanResponse(
                id=tp.id,
                beneficiary_id=tp.beneficiary_id,
                start_date=str(tp.start_date),
                end_date=str(tp.end_date),
                objective=tp.objective,
                description=tp.description,
                workload=tp.workload,
                status=tp.status
            ) for tp in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [tp.dict() for tp in therapeutic_plans]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{therapeutic_plan_id}")
@inject
async def get_therapeutic_plan_by_id(
    therapeutic_plan_id: int,
    use_case: GetTherapeuticPlanByIdUseCase = Depends(
        Provide[Container.get_therapeutic_plan_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(therapeutic_plan_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano terapêutico não encontrado"}
            )

        response_therapeutic_plan = TherapeuticPlanResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date),
            objective=response.value.objective,
            description=response.value.description,
            workload=response.value.workload,
            status=response.value.status
        )

        return JSONResponse(status_code=200, content={"data": response_therapeutic_plan.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{therapeutic_plan_id}")
@inject
async def update(
    therapeutic_plan_id: int,
    request: TherapeuticPlanRequest,
    use_case: UpdateTherapeuticPlanUseCase = Depends(
        Provide[Container.update_therapeutic_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        therapeutic_plan = TherapeuticPlan(
            id=therapeutic_plan_id,
            beneficiary_id=request.beneficiary_id,
            start_date=request.start_date,
            end_date=request.end_date,
            objective=request.objective,
            description=request.description,
            workload=request.workload,
            status=request.status
        )

        response = await use_case.execute(therapeutic_plan)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano terapêutico não encontrado"}
            )

        response_therapeutic_plan = TherapeuticPlanResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            start_date=str(response.value.start_date),
            end_date=str(response.value.end_date),
            objective=response.value.objective,
            description=response.value.description,
            workload=response.value.workload,
            status=response.value.status
        )

        return JSONResponse(status_code=200, content={"data": response_therapeutic_plan.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{therapeutic_plan_id}")
@inject
async def delete(
    therapeutic_plan_id: int,
    use_case: DeleteTherapeuticPlanUseCase = Depends(
        Provide[Container.delete_therapeutic_plan_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(therapeutic_plan_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Plano terapêutico não encontrado"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Plano terapêutico deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.create_evaluation_use_case import CreateEvaluationUseCase
from core.use_case.delete_evaluation_use_case import DeleteEvaluationUseCase
from core.use_case.get_evaluation_by_id_use_case import GetEvaluationByIdUseCase
from core.use_case.list_evaluation_use_case import ListEvaluationUseCase
from core.use_case.update_evaluation_use_case import UpdateEvaluationUseCase
from domain.schema import EvaluationRequest, EvaluationResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.evaluation import Evaluation

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.post("/create")
@inject
async def create(
    request: EvaluationRequest,
    use_case: CreateEvaluationUseCase = Depends(
        Provide[Container.create_evaluation_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        evaluation = Evaluation(
            beneficiary_id=request.beneficiary_id,
            date=request.date,
            type=request.type,
            evaluation_result=request.evaluation_result,
            details=request.details
        )
        response = await use_case.execute(evaluation)

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

        response_evaluation = EvaluationResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            date=str(response.value.date),
            type=response.value.type,
            evaluation_result=response.value.evaluation_result,
            details=response.value.details
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_evaluation.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListEvaluationUseCase = Depends(
        Provide[Container.list_evaluation_use_case],
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

        evaluations = [
            EvaluationResponse(
                id=evaluation.id,
                beneficiary_id=evaluation.beneficiary_id,
                date=str(evaluation.date),
                type=evaluation.type,
                evaluation_result=evaluation.evaluation_result,
                details=evaluation.details
            ) for evaluation in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [evaluation.dict() for evaluation in evaluations]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{evaluation_id}")
@inject
async def get_evaluation_by_id(
    evaluation_id: int,
    use_case: GetEvaluationByIdUseCase = Depends(
        Provide[Container.get_evaluation_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(evaluation_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Avaliação não encontrada"}
            )

        response_evaluation = EvaluationResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            date=str(response.value.date),
            type=response.value.type,
            evaluation_result=response.value.evaluation_result,
            details=response.value.details
        )

        return JSONResponse(status_code=200, content={"data": response_evaluation.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{evaluation_id}")
@inject
async def update(
    evaluation_id: int,
    request: EvaluationRequest,
    use_case: UpdateEvaluationUseCase = Depends(
        Provide[Container.update_evaluation_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        evaluation = Evaluation(
            id=evaluation_id,
            beneficiary_id=request.beneficiary_id,
            date=request.date,
            type=request.type,
            evaluation_result=request.evaluation_result,
            details=request.details
        )

        response = await use_case.execute(evaluation)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Avaliação não encontrada"}
            )

        response_evaluation = EvaluationResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            date=str(response.value.date),
            type=response.value.type,
            evaluation_result=response.value.evaluation_result,
            details=response.value.details
        )

        return JSONResponse(status_code=200, content={"data": response_evaluation.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{evaluation_id}")
@inject
async def delete(
    evaluation_id: int,
    use_case: DeleteEvaluationUseCase = Depends(
        Provide[Container.delete_evaluation_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(evaluation_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Avaliação não encontrada"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Avaliação deletada com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

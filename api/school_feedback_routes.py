from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from datetime import datetime
from core.kernel.container import Container
from core.use_case.create_school_feedback_use_case import CreateSchoolFeedbackUseCase
from core.use_case.delete_school_feedback_use_case import DeleteSchoolFeedbackUseCase
from core.use_case.get_school_feedback_by_id_use_case import GetSchoolFeedbackByIdUseCase
from core.use_case.list_school_feedback_use_case import ListSchoolFeedbackUseCase
from core.use_case.update_school_feedback_use_case import UpdateSchoolFeedbackUseCase
from domain.schema import SchoolFeedbackRequest, SchoolFeedbackResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.school_feedback import SchoolFeedback

router = APIRouter(prefix="/school-feedback", tags=["SchoolFeedback"])


@router.post("/create")
@inject
async def create(
    request: SchoolFeedbackRequest,
    use_case: CreateSchoolFeedbackUseCase = Depends(
        Provide[Container.create_school_feedback_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        school_feedback = SchoolFeedback(
            beneficiary_id=request.beneficiary_id,
            supervisor_id=request.supervisor_id,
            feedback_date=request.feedback_date,
            observation=request.observation,
            tracking_status=request.tracking_status
        )
        response = await use_case.execute(school_feedback)

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

        response_school_feedback = SchoolFeedbackResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            feedback_date=str(response.value.feedback_date),
            observation=response.value.observation,
            tracking_status=response.value.tracking_status
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_school_feedback.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListSchoolFeedbackUseCase = Depends(
        Provide[Container.list_school_feedback_use_case],
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

        school_feedbacks = [
            SchoolFeedbackResponse(
                id=sf.id,
                beneficiary_id=sf.beneficiary_id,
                supervisor_id=sf.supervisor_id,
                feedback_date=str(sf.feedback_date),
                observation=sf.observation,
                tracking_status=sf.tracking_status
            ) for sf in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [sf.dict() for sf in school_feedbacks]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/{school_feedback_id}")
@inject
async def get_school_feedback_by_id(
    school_feedback_id: int,
    use_case: GetSchoolFeedbackByIdUseCase = Depends(
        Provide[Container.get_school_feedback_by_id_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(school_feedback_id)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Feedback escolar não encontrado"}
            )

        response_school_feedback = SchoolFeedbackResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            feedback_date=str(response.value.feedback_date),
            observation=response.value.observation,
            tracking_status=response.value.tracking_status
        )

        return JSONResponse(status_code=200, content={"data": response_school_feedback.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.put("/update/{school_feedback_id}")
@inject
async def update(
    school_feedback_id: int,
    request: SchoolFeedbackRequest,
    use_case: UpdateSchoolFeedbackUseCase = Depends(
        Provide[Container.update_school_feedback_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        school_feedback = SchoolFeedback(
            id=school_feedback_id,
            beneficiary_id=request.beneficiary_id,
            supervisor_id=request.supervisor_id,
            feedback_date=request.feedback_date,
            observation=request.observation,
            tracking_status=request.tracking_status,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        response = await use_case.execute(school_feedback)

        if response.is_bad_request:
            return JSONResponse(
                status_code=400,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Feedback escolar não encontrado"}
            )

        response_school_feedback = SchoolFeedbackResponse(
            id=response.value.id,
            beneficiary_id=response.value.beneficiary_id,
            supervisor_id=response.value.supervisor_id,
            feedback_date=str(response.value.feedback_date),
            observation=response.value.observation,
            tracking_status=response.value.tracking_status
        )

        return JSONResponse(status_code=200, content={"data": response_school_feedback.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.delete("/delete/{school_feedback_id}")
@inject
async def delete(
    school_feedback_id: int,
    use_case: DeleteSchoolFeedbackUseCase = Depends(
        Provide[Container.delete_school_feedback_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        response = await use_case.execute(school_feedback_id)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": "Feedback escolar não encontrado"}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=200, content={"data": "Feedback escolar deletado com sucesso"})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

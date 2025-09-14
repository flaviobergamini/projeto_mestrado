from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from api.dependencies import get_current_user
from core.kernel.container import Container
from core.use_case.create_school_use_case import CreateSchoolUseCase
from core.use_case.list_school_use_case import ListSchoolUseCase
from domain.schema import SchoolRequest, SchoolResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.school import School

router = APIRouter(prefix="/school", tags=["School"])


@router.post("/create")
@inject
async def create(
    request: SchoolRequest, 
    use_case: CreateSchoolUseCase = Depends(
        Provide[Container.create_school_use_case],
    ),
    user_id: str = Depends(get_current_user),
):
    try:
        school = School (
            name=request.name,
            address=request.address,
            telephone=request.telephone,
            email=request.email,
            responsible=request.responsible
        )
        response = await use_case.execute(school)
        
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
        
        response_school = SchoolResponse (
            id=response.value.id,
            name=response.value.name,
            address=response.value.address,
            telephone=response.value.telephone,
            email=response.value.email,
            responsible=response.value.responsible
        )

        return JSONResponse(status_code=HTTP_201_CREATED, content={"data": response_school.dict()})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)

@router.get("/list")
@inject
async def list(
    use_case: ListSchoolUseCase = Depends(
        Provide[Container.list_school_use_case],
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
        
        schools = [
            SchoolResponse (
                id=school.id,
                name=school.name,
                address=school.address,
                telephone=school.telephone,
                email=school.email,
                responsible=school.responsible
            ) for school in response.value
        ]

        return JSONResponse(status_code=200, content={"data": [school.dict() for school in schools]})
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=500)
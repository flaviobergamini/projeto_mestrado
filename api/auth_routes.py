from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from domain.schema import UserLogin, UserRegister
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR

from infrastructure.models.users import User

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
@inject
async def create_user(
    request: UserRegister, 
    use_case: CreateUserUseCase = Depends (Provide[Container.create_user_use_case])
    ):
    try:
        user = User(
            name = request.name,
            email = request.email,
            password = request.password
        )

        response = await use_case.execute(user)

        if response.is_bad_request:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": response.bad_request_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_201_CREATED, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
    
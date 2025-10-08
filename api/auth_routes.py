from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from domain.schema import UserLogin, UserRegister
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_401_UNAUTHORIZED

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
    
@router.post("/login")
@inject
async def login(
    request: UserLogin, 
    use_case: LoginUserUseCase = Depends (Provide[Container.login_user_use_case])
    ):
    try:
    
        response = await use_case.execute(request.email, request.password)

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )
        
        if response.is_unauthorized:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": response.unauthorized_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_200_OK, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)
    
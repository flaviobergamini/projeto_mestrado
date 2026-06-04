from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository
from domain.schema import UserRegister, UserLogin, UpdateRoleRequest, RefreshToken

router = APIRouter(prefix="/auth", tags=["Auth"])


async def _require_admin(
    authorization: str | None,
    jwt_service: JwtService,
    user_repository: UserRepository,
):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    if jwt_service.get_role_from_token(token) != "admin":
        return None
    user_id = jwt_service.get_user_id_from_token(token)
    if not user_id:
        return None
    return await user_repository.get_by_id(user_id)


@router.post("/register", status_code=HTTP_201_CREATED)
@inject
async def register(
    request: UserRegister,
    use_case: CreateUserUseCase = Depends(Provide[Container.create_user_use_case]),
):
    try:
        result = await use_case.execute(
            username=request.username,
            password=request.password,
            full_name=request.full_name,
            role=request.role,
            municipality_id=request.municipality_id,
            school_id=request.school_id,
            teacher_id=request.teacher_id,
        )

        if result.is_bad_request:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": result.bad_request_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})

        return JSONResponse(status_code=HTTP_201_CREATED, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/login")
@inject
async def login(
    request: UserLogin,
    use_case: LoginUserUseCase = Depends(Provide[Container.login_user_use_case]),
):
    try:
        result = await use_case.execute(request.username, request.password)

        if result.is_unauthorized:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": result.unauthorized_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})

        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/refresh-token")
@inject
async def refresh_token(
    request: RefreshToken,
    use_case: RefreshTokenUseCase = Depends(Provide[Container.refresh_token_use_case]),
):
    try:
        result = await use_case.execute(request.refresh_token)

        if result.is_unauthorized:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": result.unauthorized_error})
        if result.is_not_found:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": result.not_found_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})

        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.get("/users")
@inject
async def list_users(
    authorization: str | None = Header(default=None),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        admin = await _require_admin(authorization, jwt_service, user_repository)
        if not admin:
            return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"error": "Acesso negado"})

        users = await user_repository.get_all()
        return JSONResponse(status_code=HTTP_200_OK, content=[
            {
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "municipality_id": u.municipality_id,
                "school_id": u.school_id,
                "teacher_id": u.teacher_id,
            }
            for u in users
        ])
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.patch("/users/{user_id}/role")
@inject
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    authorization: str | None = Header(default=None),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        admin = await _require_admin(authorization, jwt_service, user_repository)
        if not admin:
            return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"error": "Acesso negado"})

        user = await user_repository.get_by_id(user_id)
        if not user:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": "Usuário não encontrado"})

        user.role = request.role
        updated = await user_repository.update(user)

        return JSONResponse(status_code=HTTP_200_OK, content={
            "id": updated.id,
            "username": updated.username,
            "role": updated.role,
        })
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})

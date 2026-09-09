from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from dependency_injector.wiring import inject, Provide
from starlette.status import (
    HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR,
)

from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from core.use_case.confirm_email_use_case import ConfirmEmailUseCase
from core.use_case.resend_confirmation_use_case import ResendConfirmationUseCase
from core.use_case.forgot_password_use_case import ForgotPasswordUseCase
from core.use_case.confirm_reset_password_use_case import ConfirmResetPasswordUseCase
from core.use_case.list_users_use_case import ListUsersUseCase
from core.use_case.update_user_role_use_case import UpdateUserRoleUseCase
from api.dependencies import require_roles, get_current_user
from domain.schema import (
    UserRegister, UserLogin, ConfirmEmail, ResendConfirmation,
    ForgotPassword, ConfirmResetPassword, RefreshToken, UpdateRoleRequest,
    UpdateOwnDemographics,
)
from infrastructure.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=HTTP_201_CREATED)
@inject
async def register(
    request: UserRegister,
    current_user: dict = Depends(get_current_user),
    use_case: CreateUserUseCase = Depends(Provide[Container.create_user_use_case]),
):
    try:
        result = await use_case.execute(
            requester_role=current_user["role"],
            username=request.email,
            email=request.email,
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


@router.post("/confirm-email")
@inject
async def confirm_email(
    request: ConfirmEmail,
    use_case: ConfirmEmailUseCase = Depends(Provide[Container.confirm_email_use_case]),
):
    try:
        result = await use_case.execute(request.email, request.code)
        if result.is_bad_request:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": result.bad_request_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/resend-confirmation")
@inject
async def resend_confirmation(
    request: ResendConfirmation,
    use_case: ResendConfirmationUseCase = Depends(Provide[Container.resend_confirmation_use_case]),
):
    try:
        result = await use_case.execute(request.email)
        if result.is_bad_request:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": result.bad_request_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/login")
@inject
async def login(
    request: UserLogin,
    use_case: LoginUserUseCase = Depends(Provide[Container.login_user_use_case]),
):
    try:
        result = await use_case.execute(request.email, request.password)
        if result.is_unauthorized:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": result.unauthorized_error})
        if result.is_not_found:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": result.not_found_error})
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
        result = await use_case.execute(request.email, request.refresh_token)
        if result.is_unauthorized:
            return JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={"error": result.unauthorized_error})
        if result.is_not_found:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": result.not_found_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/forgot-password")
@inject
async def forgot_password(
    request: ForgotPassword,
    use_case: ForgotPasswordUseCase = Depends(Provide[Container.forgot_password_use_case]),
):
    try:
        result = await use_case.execute(request.email)
        if result.is_bad_request:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": result.bad_request_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.post("/confirm-reset-password")
@inject
async def confirm_reset_password(
    request: ConfirmResetPassword,
    use_case: ConfirmResetPasswordUseCase = Depends(Provide[Container.confirm_reset_password_use_case]),
):
    try:
        result = await use_case.execute(request.email, request.code, request.new_password)
        if result.is_bad_request:
            return JSONResponse(status_code=HTTP_400_BAD_REQUEST, content={"error": result.bad_request_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.get("/users")
@inject
async def list_users(
    current_user: dict = Depends(require_roles("admin")),
    use_case: ListUsersUseCase = Depends(Provide[Container.list_users_use_case]),
):
    try:
        result = await use_case.execute()
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})


@router.get("/me")
@inject
async def get_own_profile(
    current_user: dict = Depends(get_current_user),
    repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    """Retorna o perfil do usuário autenticado (inclui a demografia autodeclarada, quando houver)."""
    profile = await repo.get_by_id(current_user["user_id"])
    if not profile:
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": "Usuário não encontrado"})
    return JSONResponse(status_code=HTTP_200_OK, content=profile)


@router.put("/me/demographics")
@inject
async def update_own_demographics(
    request: UpdateOwnDemographics,
    current_user: dict = Depends(require_roles("parent")),
    repo: UserRepository = Depends(Provide[Container.user_repository]),
):
    """Responsável preenche sua própria demografia (idade, faixa de renda,
    monoparentalidade, nº de filhos e de filhos neurodivergentes) para as
    métricas de adesão do painel administrativo. Requer consentimento
    explícito (`consent: true`) — nenhum campo é salvo sem ele."""
    if not request.consent:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"error": "É necessário consentir com o uso desses dados para salvá-los."},
        )
    data = request.model_dump(exclude={"consent"}, exclude_none=True)
    updated = await repo.update_demographics(current_user["user_id"], data)
    if not updated:
        return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": "Usuário não encontrado"})
    return JSONResponse(status_code=HTTP_200_OK, content=updated)


@router.patch("/users/{user_id}/role")
@inject
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: dict = Depends(require_roles("admin")),
    use_case: UpdateUserRoleUseCase = Depends(Provide[Container.update_user_role_use_case]),
):
    try:
        result = await use_case.execute(current_user["role"], user_id, request.role)
        if result.is_not_found:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": result.not_found_error})
        if result.is_err:
            return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": result.error})
        return JSONResponse(status_code=HTTP_200_OK, content=result.value)
    except Exception:
        return JSONResponse(status_code=HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Erro interno"})

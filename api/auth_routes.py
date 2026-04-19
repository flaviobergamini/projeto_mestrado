from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse
from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.verify_email_use_case import VerifyEmailUseCase
from core.use_case.forgot_password_use_case import ForgotPasswordUseCase
from core.use_case.reset_password_use_case import ResetPasswordUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from domain.schema import UserLogin, UserRegister, VerifyEmail, ForgotPassword, ResetPassword, RefreshToken, UpdateRoleRequest
from dependency_injector.wiring import inject, Provide
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_500_INTERNAL_SERVER_ERROR, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from core.services.jwt_service import JwtService
from infrastructure.repositories.user_repository import UserRepository

from infrastructure.models.users import User, UserRole
from api.dependencies import require_roles

router = APIRouter(prefix="/auth", tags=["Auth"])

async def _get_admin_user(
    authorization: str | None,
    jwt_service: JwtService,
    user_repository: UserRepository,
):

    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ", 1)[1]

    role = jwt_service.get_role_from_token(token)

    if role != "admin":
        return None
    
    user_id = jwt_service.get_user_id_from_token(token)

    if not user_id:
        return None
    
    return await user_repository.get_by_id(int(user_id))


@router.get("/users")
@inject
async def list_users(
    authorization: str | None = Header(default=None),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        admin = await _get_admin_user(authorization, jwt_service, user_repository)

        if not admin:
            return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"error": "Acesso negado"})

        users = await user_repository.get_all()

        return JSONResponse(status_code=HTTP_200_OK, content=[
            {"id": u.id, "name": u.name, "email": u.email, "role": u.role.value, "email_verified": u.email_verified}
            for u in users
        ])
    
    except Exception:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)


@router.patch("/users/{user_id}/role")
@inject
async def update_user_role(
    user_id: int,
    request: UpdateRoleRequest,
    authorization: str | None = Header(default=None),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
    user_repository: UserRepository = Depends(Provide[Container.user_repository]),
):
    try:
        admin = await _get_admin_user(authorization, jwt_service, user_repository)

        if not admin:
            return JSONResponse(status_code=HTTP_403_FORBIDDEN, content={"error": "Acesso negado"})

        user = await user_repository.get_by_id(user_id)

        if not user:
            return JSONResponse(status_code=HTTP_404_NOT_FOUND, content={"error": "Usuário não encontrado"})

        user.role = UserRole(request.role)
        updated = await user_repository.update(user)

        return JSONResponse(status_code=HTTP_200_OK, content={
            "id": updated.id, "name": updated.name, "email": updated.email, "role": updated.role.value
        })
    
    except Exception:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)


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
            password = request.password,
            role = UserRole(request.role),
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

@router.post("/verify-email")
@inject
async def verify_email(
    request: VerifyEmail,
    use_case: VerifyEmailUseCase = Depends(Provide[Container.verify_email_use_case])
):
    try:
        response = await use_case.execute(request.token)

        if response.is_bad_request:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_200_OK, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/forgot-password")
@inject
async def forgot_password(
    request: ForgotPassword,
    use_case: ForgotPasswordUseCase = Depends(Provide[Container.forgot_password_use_case])
):
    try:
        response = await use_case.execute(request.email)

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_200_OK, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/reset-password")
@inject
async def reset_password(
    request: ResetPassword,
    use_case: ResetPasswordUseCase = Depends(Provide[Container.reset_password_use_case])
):
    try:
        response = await use_case.execute(request.access_token, request.refresh_token, request.new_password)

        if response.is_bad_request:
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={"error": response.bad_request_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_200_OK, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

_NAVBAR = """
  <header style="background:linear-gradient(135deg,#1a237e 0%,#1565c0 55%,#0288d1 100%);padding:0 24px;">
    <div style="display:flex;align-items:center;padding:14px 0;min-height:64px;">
      <svg style="width:28px;height:28px;flex-shrink:0;margin-right:12px;opacity:.92;" viewBox="0 0 24 24" fill="white">
        <path d="M20.5 11H19V7c0-1.1-.9-2-2-2h-4V3.5C13 2.12 11.88 1 10.5 1S8 2.12 8 3.5V5H4c-1.1 0-1.99.9-1.99 2v3.8H3.5c1.49 0 2.7 1.21 2.7 2.7s-1.21 2.7-2.7 2.7H2V20c0 1.1.9 2 2 2h3.8v-1.5c0-1.49 1.21-2.7 2.7-2.7s2.7 1.21 2.7 2.7V22H17c1.1 0 2-.9 2-2v-4h1.5c1.38 0 2.5-1.12 2.5-2.5S21.88 11 20.5 11z"/>
      </svg>
      <div>
        <div style="color:#fff;font-size:17px;font-weight:700;line-height:1.2;letter-spacing:.2px;">
          Sistema de Apoio — Educação Inclusiva
        </div>
        <div style="color:rgba(255,255,255,.72);font-size:10px;letter-spacing:1.2px;text-transform:uppercase;margin-top:2px;">
          Apoio ao Desenvolvimento de Crianças Autistas
        </div>
      </div>
    </div>
    <div style="height:4px;background:linear-gradient(90deg,#e53935 0%,#f57c00 20%,#fdd835 40%,#43a047 60%,#1e88e5 80%,#8e24aa 100%);margin:0 -24px;"></div>
  </header>
"""

@router.get("/confirm-email", response_class=HTMLResponse)
async def confirm_email(request: Request):
    has_error = "error" in request.query_params or "error_description" in request.query_params
    error_desc = request.query_params.get("error_description", "Link inválido ou expirado.")

    if has_error:
        html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Erro na confirmação — Sistema de Apoio</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ margin:0; background:#f5f5f5; min-height:100vh; font-family:Arial,Helvetica,sans-serif; }}
    .page-content {{ display:flex; align-items:center; justify-content:center; min-height:calc(100vh - 72px); padding:32px 16px; }}
    .card {{ border:none; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,.10); max-width:460px; width:100%; overflow:hidden; }}
    .card-icon {{ width:64px; height:64px; border-radius:50%; background:#ffebee; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; }}
  </style>
</head>
<body>
  {_NAVBAR}
  <div class="page-content">
    <div class="card">
      <div class="card-body p-4 text-center">
        <div class="card-icon">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="#d32f2f" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </div>
        <h5 class="fw-bold mb-2" style="color:#c62828;">Erro na confirmação</h5>
        <p class="text-secondary mb-3">{error_desc}</p>
        <div class="alert" style="background:#fff8e1;border-left:4px solid #f57c00;border-radius:6px;text-align:left;font-size:13px;color:#e65100;">
          Solicite um novo link de confirmação ou entre em contato com o suporte.
        </div>
      </div>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html, status_code=400)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email confirmado — Sistema de Apoio</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ margin:0; background:#f5f5f5; min-height:100vh; font-family:Arial,Helvetica,sans-serif; }}
    .page-content {{ display:flex; align-items:center; justify-content:center; min-height:calc(100vh - 72px); padding:32px 16px; }}
    .card {{ border:none; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,.10); max-width:460px; width:100%; overflow:hidden; }}
    .card-icon {{ width:64px; height:64px; border-radius:50%; background:#e8f5e9; display:flex; align-items:center; justify-content:center; margin:0 auto 16px; }}
    .badge-status {{ background:#e3f2fd; color:#1565c0; border-radius:999px; padding:5px 16px; font-size:13px; font-weight:600; display:inline-block; margin-bottom:16px; }}
  </style>
</head>
<body>
  {_NAVBAR}
  <div class="page-content">
    <div class="card">
      <div class="card-body p-4 text-center">
        <div class="card-icon">
          <svg width="32" height="32" fill="none" viewBox="0 0 24 24" stroke="#2e7d32" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
          </svg>
        </div>
        <span class="badge-status">Conta ativada com sucesso</span>
        <h5 class="fw-bold mb-2" style="color:#1565c0;">Email confirmado!</h5>
        <p class="text-secondary mb-3">
          Seu email foi verificado e sua conta está pronta para uso.<br>
          Volte ao aplicativo e faça login para continuar.
        </p>
        <hr class="my-3">
        <p class="text-muted small mb-0">Dúvidas? Entre em contato com o suporte.</p>
      </div>
    </div>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html, status_code=200)


@router.post("/refresh-token")
@inject
async def refresh_token(
    request: RefreshToken,
    use_case: RefreshTokenUseCase = Depends(Provide[Container.refresh_token_use_case])
):
    try:
        response = await use_case.execute(request.refresh_token)

        if response.is_unauthorized:
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={"error": response.unauthorized_error}
            )

        if response.is_not_found:
            return JSONResponse(
                status_code=HTTP_404_NOT_FOUND,
                content={"error": response.not_found_error}
            )

        if response.is_err:
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": response.error}
            )

        return JSONResponse(status_code=HTTP_200_OK, content=response.value)
    except:
        return JSONResponse(content={"error": "Internal server error"}, status_code=HTTP_500_INTERNAL_SERVER_ERROR)

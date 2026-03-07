from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, HTMLResponse
from core.kernel.container import Container
from core.use_case.create_user_use_case import CreateUserUseCase
from core.use_case.login_user_use_case import LoginUserUseCase
from core.use_case.verify_email_use_case import VerifyEmailUseCase
from core.use_case.forgot_password_use_case import ForgotPasswordUseCase
from core.use_case.reset_password_use_case import ResetPasswordUseCase
from core.use_case.refresh_token_use_case import RefreshTokenUseCase
from domain.schema import UserLogin, UserRegister, VerifyEmail, ForgotPassword, ResetPassword, RefreshToken
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
  <title>Erro na confirmação — Agente IA TEA</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ background: #F0F4FF; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Segoe UI', sans-serif; }}
    .card {{ border: none; border-radius: 16px; box-shadow: 0 8px 32px rgba(79,70,229,.12); max-width: 480px; width: 100%; }}
    .card-header {{ background: linear-gradient(135deg,#4F46E5,#7C3AED); border-radius: 16px 16px 0 0; padding: 2rem; text-align: center; }}
    .icon-circle {{ width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,.15); display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; }}
    .icon-circle svg {{ width: 36px; height: 36px; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <div class="icon-circle">
        <svg fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </div>
      <h4 class="text-white fw-bold mb-1">Erro na confirmação</h4>
      <p class="text-white opacity-75 mb-0 small">Agente IA TEA</p>
    </div>
    <div class="card-body p-4 text-center">
      <p class="text-secondary mb-4">{error_desc}</p>
      <p class="text-muted small">Solicite um novo link de confirmação ou entre em contato com o suporte.</p>
    </div>
  </div>
</body>
</html>"""
        return HTMLResponse(content=html, status_code=400)

    html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Email confirmado — Agente IA TEA</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { background: #F0F4FF; min-height: 100vh; display: flex; align-items: center; justify-content: center; font-family: 'Segoe UI', sans-serif; }
    .card { border: none; border-radius: 16px; box-shadow: 0 8px 32px rgba(79,70,229,.12); max-width: 480px; width: 100%; }
    .card-header { background: linear-gradient(135deg,#4F46E5,#7C3AED); border-radius: 16px 16px 0 0; padding: 2rem; text-align: center; }
    .icon-circle { width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,.15); display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem; }
    .icon-circle svg { width: 36px; height: 36px; }
    .badge-pill { background: #EEF2FF; color: #4F46E5; border-radius: 999px; padding: .35rem .9rem; font-size: .8rem; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <div class="icon-circle">
        <svg fill="none" viewBox="0 0 24 24" stroke="white" stroke-width="2.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/>
        </svg>
      </div>
      <h4 class="text-white fw-bold mb-1">Email confirmado!</h4>
      <p class="text-white opacity-75 mb-0 small">Agente IA TEA</p>
    </div>
    <div class="card-body p-4 text-center">
      <span class="badge-pill d-inline-block mb-3">Conta ativada com sucesso</span>
      <p class="text-secondary mb-4">
        Seu email foi verificado e sua conta está pronta para uso.<br>
        Volte ao aplicativo e faça login para continuar.
      </p>
      <div class="border-top pt-3">
        <p class="text-muted small mb-0">Duvidas? Entre em contato com o suporte.</p>
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

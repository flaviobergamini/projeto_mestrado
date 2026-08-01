from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dependency_injector.wiring import inject, Provide

from core.kernel.container import Container
from core.use_case.validate_token_use_case import ValidateTokenUseCase
from core.permissions.roles import is_read_only

security = HTTPBearer()


async def _resolve_user(
    credentials: HTTPAuthorizationCredentials,
    use_case: ValidateTokenUseCase,
) -> dict:
    """Valida token e retorna o perfil completo do usuário."""
    result = await use_case.execute(credentials.credentials)

    if result.is_unauthorized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.unauthorized_error)
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    if result.is_err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    return result.value


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
) -> dict:
    """Retorna o perfil completo do usuário autenticado."""
    return await _resolve_user(credentials, use_case)


@inject
async def get_current_user_read_write(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
) -> dict:
    """Bloqueia pesquisador (read-only) em endpoints de escrita."""
    user = await _resolve_user(credentials, use_case)
    if is_read_only(user["role"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pesquisador não possui permissão de escrita",
        )
    return user


def require_roles(*roles: str):
    """Exige que o usuário tenha um dos roles informados."""
    @inject
    async def check_role(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
    ) -> dict:
        user = await _resolve_user(credentials, use_case)
        if user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )
        return user
    return check_role


def require_write(*roles: str):
    """
    Exige que o usuário tenha um dos roles informados E não seja read-only.
    Combina verificação de role + bloqueio de pesquisador.
    """
    @inject
    async def check(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
    ) -> dict:
        user = await _resolve_user(credentials, use_case)
        if is_read_only(user["role"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pesquisador não possui permissão de escrita",
            )
        if roles and user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado",
            )
        return user
    return check

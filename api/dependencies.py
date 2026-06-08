from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dependency_injector.wiring import inject, Provide
from core.kernel.container import Container
from core.use_case.validate_token_use_case import ValidateTokenUseCase

security = HTTPBearer()


@inject
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
) -> dict:
    result = await use_case.execute(credentials.credentials)

    if result.is_unauthorized:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.unauthorized_error)
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.not_found_error)
    if result.is_err:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    return result.value


def require_roles(*roles: str):
    @inject
    async def check_role(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        use_case: ValidateTokenUseCase = Depends(Provide[Container.validate_token_use_case]),
    ) -> dict:
        result = await use_case.execute(credentials.credentials)

        if result.is_unauthorized:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.unauthorized_error)
        if result.is_not_found:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=result.not_found_error)
        if result.is_err:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

        if result.value["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado")

        return result.value

    return check_role

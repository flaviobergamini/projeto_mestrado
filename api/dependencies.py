from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dependency_injector.wiring import inject, Provide
from core.services.jwt_service import JwtService
from core.kernel.container import Container

security = HTTPBearer()

@inject
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_service: JwtService = Depends(Provide[Container.jwt_service]),
) -> str:
    token = credentials.credentials
    user_id = jwt_service.get_user_id_from_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    
    return user_id
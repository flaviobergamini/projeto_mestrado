"""
Middleware de autenticação por API key para o transporte SSE do MCP server.

Para o transporte stdio (Claude Desktop / processo local), autenticação não é necessária
porque o processo já está no ambiente confiável do usuário.

Para o transporte SSE (HTTP), toda requisição deve incluir:
    Authorization: Bearer <MCP_SERVER_API_KEY>

Configure MCP_SERVER_API_KEY no .env do backend. Se não for definida, o servidor
SSE operará sem autenticação (não recomendado em produção).
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# Endpoints que não requerem autenticação
_PUBLIC_PATHS = {"/", "/health", "/ping", "/docs", "/openapi.json"}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """Valida o header Authorization: Bearer <key> em todas as rotas protegidas."""

    def __init__(self, app, api_key: str) -> None:
        super().__init__(app)
        self._key = api_key

    async def dispatch(self, request: Request, call_next):
        if request.url.path in _PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"error": "Não autorizado", "detail": "Header Authorization: Bearer <key> é obrigatório."},
                status_code=401,
            )

        provided_key = auth_header[len("Bearer "):]
        if provided_key != self._key:
            return JSONResponse(
                {"error": "Não autorizado", "detail": "API key inválida."},
                status_code=401,
            )

        return await call_next(request)


def get_api_key() -> str:
    """Lê a chave de API do ambiente."""
    return os.getenv("MCP_SERVER_API_KEY", "")

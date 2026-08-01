"""Middleware that writes one row to audit_logs after every handled request."""

import base64
import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from infrastructure.database_context.database import Database
from infrastructure.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi", "/favicon")


def _decode_jwt_payload(token: str) -> dict:
    """Decode JWT payload without signature verification (for audit purposes only)."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        payload = parts[1]
        # Add padding if needed
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, database: Database):
        super().__init__(app)
        self._db = database

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _SKIP_PREFIXES):
            return response

        try:
            user_id: str | None = None
            username: str | None = None

            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                payload = _decode_jwt_payload(auth_header[7:])
                user_id = payload.get("sub")
                # Cognito access token has "username" claim
                username = payload.get("username") or payload.get("cognito:username") or payload.get("email")

            async with self._db.session() as session:
                session.add(AuditLog(
                    method=request.method,
                    path=path,
                    status_code=response.status_code,
                    user_id=user_id,
                    username=username,
                ))
                await session.commit()
        except Exception:
            logger.debug("Audit log failed silently", exc_info=True)

        return response

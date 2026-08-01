from sqlalchemy import select, func
from infrastructure.database_context.database import Database
from infrastructure.models.audit_log import AuditLog


class AuditRepository:
    def __init__(self, database: Database):
        self._db = database

    async def log(
        self,
        method: str,
        path: str,
        status_code: int,
        user_id: str | None = None,
        username: str | None = None,
    ) -> None:
        async with self._db.session() as session:
            row = AuditLog(
                method=method,
                path=path,
                status_code=status_code,
                user_id=user_id,
                username=username,
            )
            session.add(row)
            await session.commit()

    async def list_paginated(self, page: int = 1, page_size: int = 20) -> dict:
        offset = (page - 1) * page_size
        async with self._db.session() as session:
            total_result = await session.execute(select(func.count()).select_from(AuditLog))
            total = total_result.scalar() or 0

            result = await session.execute(
                select(AuditLog)
                .order_by(AuditLog.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            items = [self._to_dict(r) for r in result.scalars().all()]

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

    def _to_dict(self, row: AuditLog) -> dict:
        return {
            "id": row.id,
            "method": row.method,
            "path": row.path,
            "status_code": row.status_code,
            "user_id": row.user_id,
            "username": row.username,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }

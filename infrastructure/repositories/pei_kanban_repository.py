import uuid
from typing import Optional
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.pei_kanban_card import PeiKanbanCard

VALID_STATUSES = ("todo", "doing", "done")


def _to_dict(c: PeiKanbanCard) -> dict:
    return {
        "id": c.id,
        "student_id": c.student_id,
        "pei_id": c.pei_id,
        "status": c.status,
        "title": c.title,
        "description": c.description,
        "reaction": c.reaction,
        "source": c.source,
        "position": c.position,
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


class PeiKanbanRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(PeiKanbanCard)
                .where(PeiKanbanCard.student_id == student_id, PeiKanbanCard.deleted == False)  # noqa: E712
                .order_by(PeiKanbanCard.status, PeiKanbanCard.position, PeiKanbanCard.created_at)
            )
            return [_to_dict(c) for c in result.scalars().all()]

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            card = PeiKanbanCard(
                id=str(uuid.uuid4()),
                student_id=data["student_id"],
                pei_id=data.get("pei_id"),
                status=data.get("status") or "todo",
                title=data["title"],
                description=data.get("description"),
                reaction=data.get("reaction"),
                source=data.get("source") or "manual",
                position=data.get("position") or 0,
                created_by=data.get("created_by"),
            )
            session.add(card)
            await session.commit()
            await session.refresh(card)
            return _to_dict(card)

    async def create_many_from_pei(self, student_id: str, pei_id: str, sections: list[dict], created_by: Optional[str] = None) -> list[dict]:
        """Cria um card por seção do PEI recém-gerado, todos em 'todo'."""
        async with self.database.session() as session:
            cards = []
            for i, section in enumerate(sections):
                card = PeiKanbanCard(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    pei_id=pei_id,
                    status="todo",
                    title=section["title"][:255],
                    description=section.get("description"),
                    source="auto_pei_section",
                    position=i,
                    created_by=created_by,
                )
                session.add(card)
                cards.append(card)
            await session.commit()
            for c in cards:
                await session.refresh(c)
            return [_to_dict(c) for c in cards]

    async def update(self, card_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(PeiKanbanCard).where(PeiKanbanCard.id == card_id, PeiKanbanCard.deleted == False)  # noqa: E712
            )
            card = result.scalars().first()
            if not card:
                return None
            for field in ("status", "title", "description", "reaction", "position"):
                if field in data:
                    setattr(card, field, data[field])
            await session.commit()
            await session.refresh(card)
            return _to_dict(card)

    async def delete(self, card_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(
                select(PeiKanbanCard).where(PeiKanbanCard.id == card_id, PeiKanbanCard.deleted == False)  # noqa: E712
            )
            card = result.scalars().first()
            if not card:
                return False
            card.deleted = True
            await session.commit()
            return True

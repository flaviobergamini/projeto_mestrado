import json
import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import select
from core.constants.kanban import KANBAN_STATUSES, KANBAN_REVIEW_STATUS
from core.interfaces.i_kanban_repository import IKanbanRepository
from infrastructure.database_context.database import Database
from infrastructure.models.pei_kanban_card import PeiKanbanCard
from infrastructure.models.pei_kanban_entry import PeiKanbanEntry
from infrastructure.models.bncc import BnccSkill, StudentSkillScore, StudentSkillEvent
from core.services.skill_actions import normalize_adaptations, with_ids, dump_adaptations, flatten_actions

VALID_STATUSES = KANBAN_STATUSES  # mantido por compatibilidade


def _codes(raw: Optional[str]) -> list[str]:
    try:
        v = json.loads(raw) if raw else []
        return [str(x) for x in v] if isinstance(v, list) else []
    except Exception:
        return []


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
        "skill_id": c.skill_id,
        "adaptation": c.adaptation,
        "daily_log": c.daily_log,
        "summary": c.summary,
        "responsible_teacher_id": c.responsible_teacher_id,
        "responsible_user_id": c.responsible_user_id,
        "responsible_name": c.responsible_name,
        "photos": _codes(c.photos),
        "experience_fields": _codes(c.correlated_codes),
        "score_at_creation": c.score_at_creation,
        "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
        "position": c.position,
        "created_by": c.created_by,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


class PeiKanbanRepository(IKanbanRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(PeiKanbanCard)
                .where(PeiKanbanCard.student_id == student_id, PeiKanbanCard.deleted == False)  # noqa: E712
                .order_by(PeiKanbanCard.status, PeiKanbanCard.position, PeiKanbanCard.created_at)
            )
            cards = result.scalars().all()
            skill_ids = {c.skill_id for c in cards if c.skill_id}
            skills: dict[str, tuple[str, str, str, str]] = {}
            if skill_ids:
                rows = await session.execute(
                    select(BnccSkill.id, BnccSkill.code, BnccSkill.description, BnccSkill.area, BnccSkill.grade)
                    .where(BnccSkill.id.in_(skill_ids))
                )
                skills = {i: (c, d, a, g) for i, c, d, a, g in rows.all()}
            empty = (None, None, None, None)
            return [
                {**_to_dict(c), "skill_code": skills.get(c.skill_id, empty)[0],
                 "skill_description": skills.get(c.skill_id, empty)[1],
                 "skill_area": skills.get(c.skill_id, empty)[2], "skill_grade": skills.get(c.skill_id, empty)[3]}
                for c in cards
            ]

    async def get(self, card_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(PeiKanbanCard).where(PeiKanbanCard.id == card_id, PeiKanbanCard.deleted == False)  # noqa: E712
            )
            card = result.scalars().first()
            return _to_dict(card) if card else None

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
                responsible_teacher_id=data.get("responsible_teacher_id"),
                responsible_user_id=data.get("responsible_user_id"),
                responsible_name=data.get("responsible_name"),
            )
            session.add(card)
            await session.commit()
            await session.refresh(card)
            return _to_dict(card)

    async def create_many_from_pei(self, student_id: str, pei_id: str, sections: list[dict], created_by: Optional[str] = None) -> list[dict]:
        """Cria um card por seção do PEI recém-gerado, todos em 'todo'.

        Cada geração de PEI reproduz basicamente os mesmos títulos de seção
        (ex.: "3. Estratégias Pedagógicas") — sem checar duplicata, gerar o PEI
        de novo pro mesmo aluno empilhava um card repetido por seção a cada vez.
        Compara por título (normalizado) contra os cards já existentes e ativos
        do aluno; só cria os que ainda não têm um card correspondente."""
        async with self.database.session() as session:
            existing_result = await session.execute(
                select(PeiKanbanCard.title)
                .where(PeiKanbanCard.student_id == student_id, PeiKanbanCard.deleted == False)  # noqa: E712
            )
            existing_titles = {t.strip().lower() for (t,) in existing_result.all()}

            cards = []
            for i, section in enumerate(sections):
                title = section["title"][:255]
                if title.strip().lower() in existing_titles:
                    continue
                card = PeiKanbanCard(
                    id=str(uuid.uuid4()),
                    student_id=student_id,
                    pei_id=pei_id,
                    status="todo",
                    title=title,
                    description=section.get("description"),
                    source="auto_pei_section",
                    position=i,
                    created_by=created_by,
                )
                session.add(card)
                cards.append(card)
                existing_titles.add(title.strip().lower())
            if not cards:
                return []
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
            for field in ("status", "title", "description", "reaction", "position", "adaptation", "daily_log", "summary"):
                if field in data:
                    setattr(card, field, data[field])
            if data.get("status") == KANBAN_REVIEW_STATUS and not card.reviewed_at:
                card.reviewed_at = datetime.utcnow()
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

    async def create_from_skill(self, student_id: str, skill_id: str, created_by: Optional[str] = None,
                                only_existing: bool = False) -> list[dict]:
        """Sincroniza as ações do plano (cada uma com a adaptação e a justificativa da sua adaptação) com o Kanban.

        Cada ação tem um id estável; o card ligado a ela é ATUALIZADO quando algo muda (título, adaptação,
        justificativa), mantendo coluna, diário, fotos e resumo. Ação nova cria um card, exceto com
        only_existing=True (usado ao salvar o plano). Cards antigos, sem id, são ligados pelo título uma única vez."""
        async with self.database.session() as session:
            skill = await session.get(BnccSkill, skill_id)
            row = await session.get(StudentSkillScore, (student_id, skill_id))
            groups = normalize_adaptations(row.actions) if row else []
            if not skill or not row or (row.score or 0) >= 5:  # 5 estrelas: habilidade concluída, nada mais muda
                return []
            if any(not g["id"] or any(not a["id"] for a in g["actions"]) for g in groups):  # plano antigo: fixa os ids
                groups = with_ids(groups)
                row.actions = dump_adaptations(groups)
            items = flatten_actions(groups)
            if not items:
                return []
            existing = (await session.execute(
                select(PeiKanbanCard).where(
                    PeiKanbanCard.student_id == student_id, PeiKanbanCard.skill_id == skill_id,
                    PeiKanbanCard.deleted == False,  # noqa: E712
                )
            )).scalars().all()
            by_action = {c.action_id: c for c in existing if c.action_id}
            legacy = {c.title.strip().lower(): c for c in existing if not c.action_id}
            changed: list[PeiKanbanCard] = []
            for i, item in enumerate(items):
                line = item["action"]
                title = line[:255]
                description = item["justification"] or (line if len(line) > 255 else None)
                adaptation = item["adaptation"] or None
                card = by_action.get(item["id"]) or legacy.pop(title.lower(), None)
                r = item.get("responsible") or {}
                resp = {"responsible_teacher_id": r.get("teacher_id"), "responsible_user_id": r.get("user_id"),
                        "responsible_name": r.get("name")}
                if card:
                    values = {"action_id": item["id"], "title": title, "description": description, "adaptation": adaptation,
                              **resp}
                    if any(getattr(card, k) != v for k, v in values.items()):
                        for k, v in values.items():
                            setattr(card, k, v)
                        changed.append(card)
                    continue
                if only_existing:
                    continue
                card = PeiKanbanCard(
                    id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, status="todo", action_id=item["id"],
                    title=title, description=description, adaptation=adaptation, correlated_codes=row.correlated_codes,
                    score_at_creation=row.score, source="skill_plan", position=i, created_by=created_by, **resp,
                )
                session.add(card)
                changed.append(card)
            await session.commit()
            for c in changed:
                await session.refresh(c)
            return [_to_dict(c) for c in changed]

    # ----- fotos do diário (guarda só a chave do objeto; a URL assinada é gerada na leitura) -----
    async def _photos(self, card_id: str, change) -> Optional[dict]:
        async with self.database.session() as session:
            card = (await session.execute(
                select(PeiKanbanCard).where(PeiKanbanCard.id == card_id, PeiKanbanCard.deleted == False)  # noqa: E712
            )).scalars().first()
            if not card:
                return None
            keys = change(_codes(card.photos))
            card.photos = json.dumps(keys, ensure_ascii=False) if keys else None
            await session.commit()
            await session.refresh(card)
            return _to_dict(card)

    async def add_photo(self, card_id: str, object_key: str) -> Optional[dict]:
        return await self._photos(card_id, lambda keys: [*keys, object_key])

    async def remove_photo(self, card_id: str, object_key: str) -> Optional[dict]:
        return await self._photos(card_id, lambda keys: [k for k in keys if k != object_key])

    # ----- nota da habilidade calculada pelo Kanban -----
    @staticmethod
    async def _baseline_score(session, student_id: str, skill_id: str, current: int) -> int:
        """Nota de partida: a última marcada pela professora. Sem esse registro, a nota que a habilidade tinha antes da
        primeira mudança automática do Kanban; sem nenhuma mudança, a nota atual."""
        events = (await session.execute(
            select(StudentSkillEvent).where(
                StudentSkillEvent.student_id == student_id, StudentSkillEvent.skill_id == skill_id,
                StudentSkillEvent.kind == "score",
            ).order_by(StudentSkillEvent.created_at.desc())
        )).scalars().all()
        for e in events:
            if e.username != "kanban" and e.new_score is not None:
                return e.new_score
        automatic = [e for e in events if e.username == "kanban" and e.old_score is not None]
        return automatic[-1].old_score if automatic else current

    async def sync_skill_score(self, student_id: str, skill_id: str) -> Optional[int]:
        """Estrelas pelas ações concluídas: parte da nota que a professora marcou e reparte as estrelas que faltam
        até 5 em proporção às ações concluídas (arredondando para baixo). Nunca fica abaixo da nota de partida.
        Só vale depois que a professora marcou pelo menos 1 estrela. Devolve a nova nota, ou None se não mudou."""
        async with self.database.session() as session:
            row = await session.get(StudentSkillScore, (student_id, skill_id))
            if not row or not (row.score or 0) >= 1:
                return None
            statuses = (await session.execute(
                select(PeiKanbanCard.status).where(
                    PeiKanbanCard.student_id == student_id, PeiKanbanCard.skill_id == skill_id,
                    PeiKanbanCard.deleted == False, PeiKanbanCard.status != "archived",  # noqa: E712
                )
            )).scalars().all()
            if not statuses:
                return None
            base = max(1, min(5, await self._baseline_score(session, student_id, skill_id, row.score)))
            done = sum(1 for s in statuses if s == "done")
            new = base + ((5 - base) * done) // len(statuses)
            if new == row.score:
                return None
            session.add(StudentSkillEvent(
                id=str(uuid.uuid4()), student_id=student_id, skill_id=skill_id, kind="score",
                old_score=row.score, new_score=new, note="Nota calculada pelas ações concluídas no Kanban.",
                user_id=None, username="kanban",
            ))
            row.score = new
            await session.commit()
            return new

    # ----- lançamentos do diário da ação -----
    @staticmethod
    def _entry_dict(e: PeiKanbanEntry) -> dict:
        return {
            "id": e.id, "card_id": e.card_id, "entry_date": e.entry_date.isoformat(), "text": e.text or "", "reaction": e.reaction,
            "photos": _codes(e.photos), "created_by": e.created_by,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }

    async def list_entries(self, card_id: str) -> list[dict]:
        async with self.database.session() as session:
            rows = await session.execute(
                select(PeiKanbanEntry).where(PeiKanbanEntry.card_id == card_id)
                .order_by(PeiKanbanEntry.entry_date.desc(), PeiKanbanEntry.created_at.desc())
            )
            return [self._entry_dict(e) for e in rows.scalars().all()]

    async def get_entry(self, card_id: str, entry_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            e = await session.get(PeiKanbanEntry, entry_id)
            return self._entry_dict(e) if e and e.card_id == card_id else None

    async def add_entry(self, card_id: str, entry_date: date, text: str, author: Optional[str], author_id: Optional[str],
                        reaction: Optional[int] = None) -> dict:
        async with self.database.session() as session:
            e = PeiKanbanEntry(id=str(uuid.uuid4()), card_id=card_id, entry_date=entry_date, text=text,
                               created_by=author, created_by_user_id=author_id, reaction=reaction)
            session.add(e)
            await session.commit()
            await session.refresh(e)
            return self._entry_dict(e)

    async def update_entry(self, card_id: str, entry_id: str, entry_date: Optional[date], text: Optional[str],
                           reaction: Optional[int] = None, set_reaction: bool = False) -> Optional[dict]:
        async with self.database.session() as session:
            e = await session.get(PeiKanbanEntry, entry_id)
            if not e or e.card_id != card_id:
                return None
            if entry_date is not None:
                e.entry_date = entry_date
            if text is not None:
                e.text = text
            if set_reaction:  # permite limpar a reação (None) sem confundir com 'não enviado'
                e.reaction = reaction
            await session.commit()
            await session.refresh(e)
            return self._entry_dict(e)

    async def delete_entry(self, card_id: str, entry_id: str) -> list[str]:
        """Apaga o lançamento e devolve as chaves das fotos (para remover do storage). None se não existir."""
        async with self.database.session() as session:
            e = await session.get(PeiKanbanEntry, entry_id)
            if not e or e.card_id != card_id:
                return None  # type: ignore[return-value]
            keys = _codes(e.photos)
            await session.delete(e)
            await session.commit()
            return keys

    async def _entry_photos(self, card_id: str, entry_id: str, change) -> Optional[dict]:
        async with self.database.session() as session:
            e = await session.get(PeiKanbanEntry, entry_id)
            if not e or e.card_id != card_id:
                return None
            keys = change(_codes(e.photos))
            e.photos = json.dumps(keys, ensure_ascii=False) if keys else None
            await session.commit()
            await session.refresh(e)
            return self._entry_dict(e)

    async def add_entry_photo(self, card_id: str, entry_id: str, object_key: str) -> Optional[dict]:
        return await self._entry_photos(card_id, entry_id, lambda keys: [*keys, object_key])

    async def remove_entry_photo(self, card_id: str, entry_id: str, object_key: str) -> Optional[dict]:
        return await self._entry_photos(card_id, entry_id, lambda keys: [k for k in keys if k != object_key])

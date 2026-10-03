from typing import Optional
from sqlalchemy import select, delete, func
from infrastructure.database_context.database import Database
from infrastructure.models.user_profile import UserProfile
from infrastructure.models.municipality import Municipality
from infrastructure.models.school import School
from infrastructure.models.user_school import UserSchool
from core.interfaces.i_user_repository import IUserRepository


def _to_dict(u: UserProfile) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "full_name": u.full_name,
        "role": u.role,
        "is_active": u.is_active,
        "municipality_id": u.municipality_id,
        "school_id": u.school_id,
        "teacher_id": u.teacher_id,
        "birth_year": u.birth_year,
        "income_bracket": u.income_bracket,
        "single_parent": u.single_parent,
        "children_count": u.children_count,
        "neurodivergent_children_count": u.neurodivergent_children_count,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


async def _attach_school_ids(session, users: list[dict]) -> list[dict]:
    """Preenche school_ids (todas as escolas do usuário). Sem linhas em user_schools,
    cai para a escola principal, se houver."""
    ids = [u["id"] for u in users]
    by_user: dict[str, list[str]] = {}
    if ids:
        rows = await session.execute(
            select(UserSchool.user_id, UserSchool.school_id).where(UserSchool.user_id.in_(ids))
        )
        for user_id, school_id in rows.all():
            by_user.setdefault(user_id, []).append(school_id)
    for u in users:
        found = by_user.get(u["id"])
        u["school_ids"] = found if found else ([u["school_id"]] if u["school_id"] else [])
    return users


def _requested_school_ids(school_ids: Optional[list[str]], school_id: Optional[str], school_id_given: bool) -> Optional[list[str]]:
    """Lista de escolas pedida, sem duplicatas e na ordem recebida (a primeira é a
    principal). None = não mexe nas escolas. `school_id` sozinho equivale a [school_id]."""
    if school_ids is not None:
        ids = school_ids
    elif school_id_given:
        ids = [school_id] if school_id else []
    else:
        return None
    return list(dict.fromkeys(i for i in ids if i))


async def _replace_user_schools(session, user: UserProfile, school_ids: list[str]) -> None:
    user.school_id = school_ids[0] if school_ids else None
    await session.execute(delete(UserSchool).where(UserSchool.user_id == user.id))
    session.add_all(UserSchool(user_id=user.id, school_id=sid) for sid in school_ids)


class UserRepository(IUserRepository):
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(
        self,
        id: str,
        username: str,
        full_name: Optional[str],
        role: str,
        municipality_id: Optional[str],
        school_id: Optional[str],
        teacher_id: Optional[str],
        is_active: bool = True,
        school_ids: Optional[list[str]] = None,
    ) -> dict:
        async with self.database.session() as session:
            # Check for soft-deleted record with same username
            existing_result = await session.execute(
                select(UserProfile).where(UserProfile.username == username, UserProfile.deleted == True)
            )
            existing = existing_result.scalars().first()
            if existing:
                existing.id = id
                existing.full_name = full_name
                existing.role = role
                existing.municipality_id = municipality_id
                existing.teacher_id = teacher_id
                existing.is_active = is_active
                existing.deleted = False
                await _replace_user_schools(
                    session, existing, _requested_school_ids(school_ids, school_id, True) or [])
                await session.commit()
                await session.refresh(existing)
                return (await _attach_school_ids(session, [_to_dict(existing)]))[0]

            user = UserProfile(
                id=id,
                username=username,
                full_name=full_name,
                role=role,
                municipality_id=municipality_id,
                teacher_id=teacher_id,
                is_active=is_active,
            )
            session.add(user)
            await session.flush()
            await _replace_user_schools(
                session, user, _requested_school_ids(school_ids, school_id, True) or [])
            await session.commit()
            await session.refresh(user)
            return (await _attach_school_ids(session, [_to_dict(user)]))[0]

    async def update_role(self, user_id: str, role: str) -> dict:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            user.role = role
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def update(self, user_id: str, full_name: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None, links: Optional[dict] = None) -> dict | None:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            if full_name is not None:
                user.full_name = full_name
            if role is not None:
                user.role = role
            if is_active is not None:
                user.is_active = is_active
            # links traz só as chaves enviadas; valor None/"" limpa o vínculo.
            for key in ("municipality_id", "teacher_id"):
                if links and key in links:
                    setattr(user, key, links[key] or None)
            requested = _requested_school_ids(
                (links or {}).get("school_ids"), (links or {}).get("school_id"), bool(links) and "school_id" in links)
            if requested is not None:
                await _replace_user_schools(session, user, requested)
            await session.commit()
            await session.refresh(user)
            return (await _attach_school_ids(session, [_to_dict(user)]))[0]

    async def update_username(self, user_id: str, new_username: str) -> Optional[dict]:
        """Atualiza o e-mail de login armazenado localmente (username == email).
        Chamar SEMPRE depois de IAuthService.update_email ter sucesso no Cognito —
        senão o perfil local fica com um e-mail que o Cognito não reconhece mais
        pra login (get_by_username em login_user_use_case não acharia o perfil)."""
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            user.username = new_username
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def update_demographics(self, user_id: str, data: dict) -> Optional[dict]:
        """Atualiza a demografia autodeclarada do responsável (role="parent"), usada
        nas métricas de nível de adesão do painel administrativo. Preenchida pelo
        próprio responsável, com consentimento explícito, nunca por um admin."""
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            if not user:
                return None
            for field in ("birth_year", "income_bracket", "single_parent", "children_count", "neurodivergent_children_count"):
                if field in data:
                    setattr(user, field, data[field])
            await session.commit()
            await session.refresh(user)
            return _to_dict(user)

    async def delete(self, user_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id))
            user = result.scalar_one_or_none()
            if not user:
                return False
            user.deleted = True
            await session.commit()
            return True

    async def get_by_username(self, username: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.username == username, UserProfile.deleted == False))
            user = result.scalars().first()
            return (await _attach_school_ids(session, [_to_dict(user)]))[0] if user else None

    async def get_by_id(self, user_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.id == user_id, UserProfile.deleted == False))
            user = result.scalars().first()
            return (await _attach_school_ids(session, [_to_dict(user)]))[0] if user else None

    async def get_all(self) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(UserProfile).where(UserProfile.deleted == False).order_by(UserProfile.username))
            return [_to_dict(u) for u in result.scalars().all()]

    async def list_by_role(self, role: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(UserProfile)
                .where(UserProfile.role == role, UserProfile.deleted == False)
                .order_by(UserProfile.full_name, UserProfile.username)
            )
            return [_to_dict(u) for u in result.scalars().all()]

    async def list_paginated(self, page: int = 1, page_size: int = 20, role: str | None = None) -> dict:
        offset = (page - 1) * page_size
        async with self.database.session() as session:
            filters = [UserProfile.deleted == False]
            if role:
                filters.append(UserProfile.role == role)

            total_result = await session.execute(select(func.count()).select_from(UserProfile).where(*filters))
            total = total_result.scalar() or 0

            result = await session.execute(
                select(UserProfile)
                .where(*filters)
                .order_by(UserProfile.username)
                .offset(offset)
                .limit(page_size)
            )
            items = await _attach_school_ids(session, [_to_dict(u) for u in result.scalars().all()])

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": max(1, (total + page_size - 1) // page_size),
        }

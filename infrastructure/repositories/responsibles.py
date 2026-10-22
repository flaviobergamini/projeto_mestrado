"""Professores responsáveis: a hierarquia de cada aluno (responsável 1, 2, 3...) e o preenchimento dos nomes."""
from typing import Optional
from sqlalchemy import select
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.models.user_profile import UserProfile


async def _users_by_teacher(session, teacher_ids: list[str]) -> dict[str, str]:
    if not teacher_ids:
        return {}
    rows = await session.execute(
        select(UserProfile.teacher_id, UserProfile.id).where(
            UserProfile.teacher_id.in_(teacher_ids), UserProfile.deleted == False,  # noqa: E712
        ).order_by(UserProfile.created_at)
    )
    out: dict[str, str] = {}
    for teacher_id, user_id in rows.all():
        out.setdefault(teacher_id, user_id)
    return out


async def student_responsibles(session, student_id: str) -> list[dict]:
    """Professores vinculados ao aluno, do responsável 1 em diante."""
    rows = (await session.execute(
        select(TeacherStudentLink, Teacher)
        .join(Teacher, Teacher.id == TeacherStudentLink.teacher_id)
        .where(TeacherStudentLink.student_id == student_id, TeacherStudentLink.deleted == False,  # noqa: E712
               Teacher.deleted == False)  # noqa: E712
    )).all()
    rows = sorted(rows, key=lambda r: (r[0].rank is None, r[0].rank or 0, r[0].created_at))
    users = await _users_by_teacher(session, [t.id for _, t in rows])
    return [{"teacher_id": t.id, "name": t.name, "rank": i + 1, "user_id": users.get(t.id)} for i, (_, t) in enumerate(rows)]


async def default_responsible(session, student_id: str) -> Optional[dict]:
    """O 'responsável 1' do aluno (o primeiro da lista) — padrão quando quem cria não é um professor."""
    first = next(iter(await student_responsibles(session, student_id)), None)
    return {"teacher_id": first["teacher_id"], "user_id": first["user_id"], "name": first["name"]} if first else None


async def fill_responsibles(session, groups: list[dict]) -> list[dict]:
    """Completa nome e usuário dos responsáveis que chegaram só com o teacher_id (troca feita pela coordenação)."""
    need = {g["responsible"]["teacher_id"] for g in groups
            if g.get("responsible") and g["responsible"].get("teacher_id") and not g["responsible"].get("name")}
    if not need:
        return groups
    teachers = {t.id: t for t in (await session.execute(select(Teacher).where(Teacher.id.in_(need)))).scalars().all()}
    users = await _users_by_teacher(session, list(need))
    out = []
    for g in groups:
        r = g.get("responsible")
        if r and r.get("teacher_id") in need:
            t = teachers.get(r["teacher_id"])
            r = {"teacher_id": r["teacher_id"], "user_id": users.get(r["teacher_id"]), "name": t.name if t else None}
            g = {**g, "responsible": r}
        out.append(g)
    return out

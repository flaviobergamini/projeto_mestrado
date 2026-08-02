from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from dependency_injector.wiring import inject, Provide
from sqlalchemy import select

from api.dependencies import get_current_user, get_current_user_read_write
from core.kernel.container import Container
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.models.school import School

router = APIRouter(prefix="/students", tags=["Students"])


class StudentCreate(BaseModel):
    name: str
    school_id: Optional[str] = None
    birth_date: Optional[str] = None
    age: Optional[str] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    guardians: Optional[list[str]] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    school_id: Optional[str] = None
    birth_date: Optional[str] = None
    age: Optional[str] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    guardians: Optional[list[str]] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None


@router.get("/schools-list")
@inject
async def list_schools_for_students(
    current_user: dict = Depends(get_current_user),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    """Retorna id+nome de todas as escolas para popular selects no formulário."""
    async with repo.database.session() as session:
        result = await session.execute(select(School.id, School.name).order_by(School.name))
        return [{"id": row.id, "name": row.name} for row in result.all()]


@router.get("")
@inject
async def list_students(
    school_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    user_school = current_user.get("school_id")
    filter_school = school_id or (user_school if current_user["role"] not in ("admin", "secretaria", "pesquisador") else None)
    return await repo.list_all(school_id=filter_school)


@router.get("/{student_id}")
@inject
async def get_student(
    student_id: str,
    current_user: dict = Depends(get_current_user),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    student = await repo.get_by_id(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return student


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_student(
    body: StudentCreate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    data = body.model_dump()
    if data.get('grade'): data['grade'] = data['grade'].upper()
    if data.get('class_name'): data['class_name'] = data['class_name'].upper()
    return await repo.create(data)


@router.put("/{student_id}")
@inject
async def update_student(
    student_id: str,
    body: StudentUpdate,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    data = body.model_dump(exclude_none=True)
    if data.get('grade'): data['grade'] = data['grade'].upper()
    if data.get('class_name'): data['class_name'] = data['class_name'].upper()
    updated = await repo.update(student_id, data)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return updated


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_student(
    student_id: str,
    current_user: dict = Depends(get_current_user_read_write),
    repo: StudentRepository = Depends(Provide[Container.student_repository]),
):
    deleted = await repo.delete(student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")

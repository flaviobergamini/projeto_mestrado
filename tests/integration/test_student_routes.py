"""Testa a rota de alunos de ponta a ponta via TestClient, sem banco de dados
real: o repositório é substituído por um fake em memória (override do
container de DI) e a autenticação é substituída por um usuário fixo (override
de dependency do FastAPI). Isso isola o que a rota realmente decide — como o
uppercase forçado de grade/class_name — do resto da stack de infraestrutura.
"""

import pytest
from fastapi.testclient import TestClient

from api.dependencies import get_current_user, get_current_user_read_write
from main import app


class FakeStudentRepository:
    """Repositório em memória — mesma interface pública de StudentRepository,
    sem tocar em banco de dados."""

    def __init__(self):
        self._students: dict[str, dict] = {}
        self._counter = 0

    async def list_all(self, school_id=None):
        return list(self._students.values())

    async def get_by_id(self, student_id):
        return self._students.get(student_id)

    async def create(self, data: dict) -> dict:
        self._counter += 1
        student_id = f"student-{self._counter}"
        record = {"id": student_id, **data}
        self._students[student_id] = record
        return record

    async def update(self, student_id: str, data: dict):
        if student_id not in self._students:
            return None
        self._students[student_id].update(data)
        return self._students[student_id]

    async def delete(self, student_id: str) -> bool:
        return self._students.pop(student_id, None) is not None


ADMIN_USER = {
    "user_id": "admin-1",
    "username": "admin@example.com",
    "full_name": "Admin de Teste",
    "role": "admin",
    "is_active": True,
}


@pytest.fixture
def client():
    fake_repo = FakeStudentRepository()

    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    app.dependency_overrides[get_current_user_read_write] = lambda: ADMIN_USER
    app.container.student_repository.override(fake_repo)

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    app.container.student_repository.reset_override()


def test_create_student_forces_grade_and_class_name_uppercase(client):
    response = client.post(
        "/students",
        json={
            "name": "João da Silva",
            "grade": "5º ano",
            "class_name": "a",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["grade"] == "5º ANO"
    assert body["class_name"] == "A"


def test_create_student_without_grade_or_class_name_does_not_fail(client):
    response = client.post("/students", json={"name": "Ana Pereira"})
    assert response.status_code == 201
    body = response.json()
    assert body.get("grade") is None
    assert body.get("class_name") is None


def test_update_student_forces_grade_and_class_name_uppercase(client):
    created = client.post("/students", json={"name": "Pedro Costa"}).json()
    student_id = created["id"]

    response = client.put(
        f"/students/{student_id}",
        json={"grade": "3º ano", "class_name": "b"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["grade"] == "3º ANO"
    assert body["class_name"] == "B"


def test_update_nonexistent_student_returns_404(client):
    response = client.put("/students/does-not-exist", json={"name": "Alguém"})
    assert response.status_code == 404


def test_get_nonexistent_student_returns_404(client):
    response = client.get("/students/does-not-exist")
    assert response.status_code == 404


def test_list_students_returns_created_ones(client):
    client.post("/students", json={"name": "Aluno 1"})
    client.post("/students", json={"name": "Aluno 2"})

    response = client.get("/students")
    assert response.status_code == 200
    names = {s["name"] for s in response.json()}
    assert {"Aluno 1", "Aluno 2"} <= names

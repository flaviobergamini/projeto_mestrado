"""A escola e os docentes voltam como nome na resposta da IA mesmo quando a fonte deles não foi marcada."""
import asyncio
from types import SimpleNamespace

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize

STUDENT = SimpleNamespace(id="stu-1", school_id="sch-1", name="Ana Silva", age=6, grade="1", class_name="A", diagnosis="TEA",
                          anonymized_data=None)
SCHOOL = SimpleNamespace(id="sch-1", name="Escola Sol", institution_type="municipal")
TEACHER = SimpleNamespace(id="tea-1", name="Profa. Bia", school_id="sch-1", specialization="AEE")


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows

    def first(self):
        return self.rows[0] if self.rows else None


class _Session:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def get(self, model, key):
        return {"Student": STUDENT, "School": SCHOOL}.get(model.__name__)

    async def execute(self, query, *a):
        if "teacher_student_links" in str(query):
            return _Result([SimpleNamespace(teacher=TEACHER)])
        return _Result([])


def test_school_and_teacher_ids_are_replaced_even_without_their_sources():
    service = AnonymizationService(SimpleNamespace(session=_Session))
    context, name_map = asyncio.run(service.build_context("stu-1", sources=["student"]))
    answer = deanonymize("A escola sch-1 apoia stu-1 com tea-1.", name_map)
    assert answer == "A escola Escola Sol apoia Ana Silva com Profa. Bia."
    assert "Escola Sol" not in context and "Bia" not in context and "=== ESCOLA" not in context and "DOCENTES" not in context

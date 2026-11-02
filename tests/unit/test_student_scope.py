import core.kernel.container  # noqa: F401  (carrega o container primeiro: evita import circular de core.kernel)
from sqlalchemy.dialects import postgresql

from api.student_access import student_scope_condition


def sql(user):
    cond = student_scope_condition(user)
    return None if cond is None else str(cond.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_admin_sees_every_student():
    assert sql({"role": "admin"}) is None
    assert sql({"role": "viewer"}) is None


def test_professor_only_sees_linked_students():
    q = sql({"role": "professor", "teacher_id": "t1"})
    assert "teacher_student_links" in q and "'t1'" in q
    assert "school" not in q.lower().replace("student_links", "")  # não amplia para a escola inteira


def test_professor_without_teacher_sees_nothing():
    assert sql({"role": "professor", "teacher_id": None}) == "false"


def test_coordination_secretary_parent_and_therapist_scopes():
    assert "'s1'" in sql({"role": "coordenacao", "school_ids": ["s1"]})
    assert sql({"role": "coordenacao", "school_ids": []}) == "false"
    assert "'m1'" in sql({"role": "secretaria", "municipality_id": "m1"})
    assert sql({"role": "secretaria"}) == "false"
    assert "parent_student_links" in sql({"role": "parent", "user_id": "u1"})
    assert "therapist_student_links" in sql({"role": "therapist", "user_id": "u2"})


def test_unknown_role_sees_nothing():
    assert sql({"role": "qualquer"}) == "false"

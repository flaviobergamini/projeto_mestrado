"""Perfil funcional: uma geração por semestre por aluno; apagar libera uma nova."""
import asyncio
from datetime import date, datetime

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.services.semester import same_semester, semester_bounds
from core.use_case.functional_profile.functional_profile_use_cases import GenerateFunctionalProfileUseCase


def test_semester_bounds():
    assert semester_bounds(date(2026, 3, 10)) == (date(2026, 1, 1), date(2026, 6, 30))
    assert semester_bounds(date(2026, 10, 22)) == (date(2026, 7, 1), date(2026, 12, 31))
    assert same_semester(datetime(2026, 7, 1, 0, 0), date(2026, 10, 22)) and not same_semester("2026-06-30T23:59:00", date(2026, 10, 22))


class Students:
    async def get_by_id(self, sid):
        return {"id": sid, "school_id": None}


class Repo:
    def __init__(self, existing):
        self.existing, self.created = existing, False

    async def list_for_student(self, sid):
        return self.existing

    async def create(self, *a, **k):
        self.created = True
        return {"id": "p"}


class Ai:
    called = False

    async def build_context(self, sid, sources):
        Ai.called = True
        return "", {}


def _run(existing):
    repo = Repo(existing)
    res = asyncio.run(GenerateFunctionalProfileUseCase(repo, Students(), None, Ai(), None).execute("s1", {"user_id": "u"}))
    return res, repo


def test_blocks_second_ai_profile_in_the_same_semester_without_calling_the_model():
    Ai.called = False
    res, repo = _run([{"origin": "ai", "created_at": datetime.now().isoformat()}])
    assert res.is_bad_request and "semestre" in res.bad_request_error and not Ai.called and not repo.created


def test_manual_or_previous_semester_profiles_do_not_block():
    Ai.called = False
    try:
        _run([{"origin": "manual", "created_at": datetime.now().isoformat()},
              {"origin": "ai", "created_at": datetime(date.today().year - 1, 1, 15).isoformat()}])
    except AttributeError:
        pass  # o teste para depois da trava (os fakes não implementam o resto do fluxo da IA)
    assert Ai.called  # passou da trava e chegou ao contexto da IA

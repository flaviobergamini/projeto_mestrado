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

    async def build_context(self, sid, sources, **kwargs):
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


class Settings:
    def __init__(self, months):
        self.months = months

    async def get(self, key, default):
        return {"interval_months": self.months}


def test_admin_interval_controls_when_a_new_profile_is_allowed():
    from core.services.semester import same_period
    today = date(2026, 11, 25)
    assert same_period("2026-07-01T00:00:00", today, 6) and not same_period("2026-07-01T00:00:00", today, 3)
    assert same_period("2026-11-02T00:00:00", today, 1) and not same_period("2026-10-31T00:00:00", today, 1)
    assert not same_period(today, today, 0)
    now = [{"origin": "ai", "created_at": datetime.now().isoformat()}]
    for months, blocked in ((0, False), (6, True), (1, True)):
        Ai.called = False
        uc = GenerateFunctionalProfileUseCase(Repo(now), Students(), None, Ai(), None, settings=Settings(months))
        try:
            asyncio.run(uc.execute("s1", {"user_id": "u"}))
        except AttributeError:
            pass
        assert Ai.called is (not blocked), months


def test_pdf_is_generated_only_for_the_student_of_the_profile():
    from core.use_case.functional_profile.functional_profile_use_cases import RenderProfilePdfUseCase
    from infrastructure.services.report_pdf_generator import ReportPdfGenerator
    profile = {"student_id": "s1", "title": "P <1>", "origin": "ai", "created_at": "2026-11-25T10:00:00",
               "content": {"summary": "a & b", "evidence": ["e"], "domains": [
                   {"label": "Comunicação", "level": None, "description": "d", "strengths": ["s"], "needs": [], "supports": [], "bncc_references": ["EI03EO01"]}]}}

    class Profiles:
        async def get(self, pid):
            return profile

    uc = RenderProfilePdfUseCase(Profiles(), Students(), ReportPdfGenerator())
    ok = asyncio.run(uc.execute("s1", "p1"))
    assert ok.is_ok and ok.value[:4] == b"%PDF"
    assert asyncio.run(uc.execute("outro", "p1")).is_not_found

"""Resumo da habilidade por IA: respeita 'não trabalhar com a IA', anonimiza o pedido e devolve o texto sem salvar."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (carrega o pacote core.kernel na ordem certa; evita import circular)
from core.use_case.skill_plan.generate_skill_summary_use_case import GenerateSkillSummaryUseCase


class FakeStudents:
    async def get_by_id(self, student_id):
        return {"id": student_id} if student_id == "s1" else None


class FakeRepo:
    def __init__(self, ctx):
        self.ctx = ctx

    async def skill_context(self, student_id, skill_id):
        return self.ctx


class FakeAi:
    def __init__(self):
        self.calls = []

    async def build_context(self, student_id, sources):
        return "ctx", {"UUID-1": "Maria"}

    async def generate_text(self, operation, system_instruction, prompt, user_id):
        self.calls.append((operation, system_instruction, prompt))
        return "O aluno UUID-1 está em progresso."

    def reanonymize(self, text, name_map):
        for k, v in name_map.items():
            text = text.replace(v, k)
        return text

    def deanonymize(self, text, name_map):
        for k, v in name_map.items():
            text = text.replace(k, v)
        return text


class FakePrompts:
    async def get(self, scope):
        return f"prompt:{scope}"


def _ctx(**kw):
    base = {"code": "EI03EO01", "description": "d", "grade": "Infantil", "area": "a", "score": 3, "ai_excluded": False,
            "observation": "Maria brincou bem", "adaptation": "", "justification": "", "actions": "",
            "cards": [], "score_history": []}
    return {**base, **kw}


def _run(ctx):
    ai = FakeAi()
    uc = GenerateSkillSummaryUseCase(FakeRepo(ctx), FakeStudents(), ai, FakePrompts())
    return asyncio.run(uc.execute("s1", "k1", {"user_id": "u"})), ai


def test_returns_deanonymized_summary_and_uses_editable_prompt():
    result, ai = _run(_ctx())
    assert result.is_ok and result.value["summary"] == "O aluno Maria está em progresso."
    op, system, prompt = ai.calls[0]
    assert (op, system) == ("skill_summary", "prompt:skill_summary")
    assert "Maria" not in prompt and "UUID-1" in prompt  # nome real não vai ao modelo


def test_skill_marked_no_ai_is_never_sent_to_the_model():
    result, ai = _run(_ctx(ai_excluded=True))
    assert result.is_bad_request and ai.calls == []


def test_unknown_student_or_skill():
    ai = FakeAi()
    uc = GenerateSkillSummaryUseCase(FakeRepo(None), FakeStudents(), ai, FakePrompts())
    assert asyncio.run(uc.execute("zzz", "k1", {})).is_not_found
    assert asyncio.run(uc.execute("s1", "k1", {})).is_not_found
    assert ai.calls == []

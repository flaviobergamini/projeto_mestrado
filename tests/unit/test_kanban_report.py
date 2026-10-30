import asyncio
import core.kernel.container  # noqa: F401  (carrega o container primeiro: evita import circular de core.kernel)

from core.use_case.kanban.kanban_use_cases import RenderKanbanReportUseCase


def card(cid, status, grade, area, code, updated="2026-10-20T10:00:00", teacher="t1"):
    return {"id": cid, "status": status, "title": f"Ação {cid}", "skill_grade": grade, "skill_area": area, "skill_code": code,
            "skill_description": "Desc", "updated_at": updated, "responsible_teacher_id": teacher, "responsible_user_id": None,
            "responsible_name": "Ana"}


class Repo:
    def __init__(self, cards):
        self.cards = cards

    async def list_by_student(self, student_id):
        return self.cards

    async def list_entries(self, card_id):
        return [{"entry_date": "2026-10-20", "text": "fez", "reaction": 4}, {"entry_date": "2026-01-01", "text": "antigo", "reaction": None}]


class Students:
    async def get_by_id(self, student_id):
        return {"id": student_id, "name": "Aluno"}


class Pdf:
    def kanban_report(self, report, name):
        self.report = report
        return b"%PDF"


ADMIN = {"user_id": "u", "role": "admin", "username": "a"}


def run(cards, filters):
    pdf = Pdf()
    res = asyncio.run(RenderKanbanReportUseCase(Repo(cards), Students(), pdf).execute("s1", filters, ADMIN))
    return res, pdf


CARDS = [
    card("1", "todo", "1º ano", "Língua Portuguesa", "EF01LP01"),
    card("2", "done", "1º ano", "Matemática", "EF01MA01", updated="2026-10-20T10:00:00"),
    card("3", "done", "2º ano", "Matemática", "EF02MA01", updated="2026-01-05T10:00:00"),
    card("4", "doing", "2º ano", "Língua Portuguesa", "EF02LP01"),
]


def test_columns_grades_areas_and_period_filters():
    res, pdf = run(CARDS, {"statuses": ["done"], "date_from": "2026-10-01"})
    assert res.is_ok and [c["id"] for g in pdf.report["groups"] for s in g["skills"] for c in s["cards"]] == ["2"]

    _, pdf = run(CARDS, {"grades": ["2º ano"], "areas": ["Língua Portuguesa"]})
    assert [c["id"] for g in pdf.report["groups"] for s in g["skills"] for c in s["cards"]] == ["4"]

    _, pdf = run(CARDS, {})  # sem filtros: todas as colunas, sem período
    assert pdf.report["counts"] == {"todo": 1, "doing": 1, "done": 2, "archived": 0}


def test_entries_follow_the_period():
    _, pdf = run(CARDS, {"statuses": ["done"], "date_from": "2026-10-01", "include_entries": True})
    entries = pdf.report["groups"][0]["skills"][0]["cards"][0]["entries"]
    assert [e["text"] for e in entries] == ["fez"]


def test_other_teachers_cards_are_hidden_from_professor():
    pdf = Pdf()
    prof = {"user_id": "u2", "role": "professor", "username": "p", "teacher_id": "t2"}
    asyncio.run(RenderKanbanReportUseCase(Repo(CARDS), Students(), pdf).execute("s1", {}, prof))
    assert pdf.report["counts"] == {"todo": 0, "doing": 0, "done": 0, "archived": 0}


def test_real_pdf_renders():
    from infrastructure.services.kanban_report_pdf import generate_kanban_report_pdf
    _, pdf = run(CARDS, {"include_entries": True})
    assert generate_kanban_report_pdf(pdf.report, "Aluno Teste")[:4] == b"%PDF"

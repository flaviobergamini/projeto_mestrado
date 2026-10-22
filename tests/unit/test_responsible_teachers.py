"""Professor responsável: quem cria é o dono, só a coordenação troca, cada professor vê só os seus cards."""
import asyncio

from core.kernel.container import Container  # noqa: F401  (evita import circular)
from core.services.skill_actions import (
    actor_from_user, card_responsible, merge_adaptations, normalize_adaptations, owns, own_responsible,
)
from core.use_case.kanban.kanban_use_cases import ListKanbanCardsUseCase, UpdateKanbanCardUseCase

ANA = {"user_id": "u-ana", "teacher_id": "t-ana", "role": "professor", "full_name": "Ana"}
BIA = {"user_id": "u-bia", "teacher_id": "t-bia", "role": "professor", "full_name": "Bia"}
COORD = {"user_id": "u-c", "teacher_id": None, "role": "coordenacao", "full_name": "Coord"}
R_ANA = {"teacher_id": "t-ana", "user_id": "u-ana", "name": "Ana"}
R_BIA = {"teacher_id": "t-bia", "user_id": "u-bia", "name": "Bia"}
DEFAULT = {"teacher_id": "t-1", "user_id": "u-1", "name": "Responsável 1"}


def _g(i, text, responsible):
    return {"id": i, "adaptation": text, "justification": "", "responsible": responsible, "actions": [{"id": i + "-a", "action": "x"}]}


def test_teacher_who_creates_becomes_responsible_and_coordination_uses_default():
    new = [{"id": "", "adaptation": "nova", "justification": "", "responsible": R_BIA, "actions": []}]
    by_teacher = merge_adaptations([], new, actor_from_user(ANA), DEFAULT)
    assert by_teacher[0]["responsible"] == R_ANA          # o que ele mandou em `responsible` é ignorado
    by_coord = merge_adaptations([], [{**new[0], "responsible": None}], actor_from_user(COORD), DEFAULT)
    assert by_coord[0]["responsible"] == DEFAULT           # coordenação criando: responsável 1 do aluno


def test_teacher_cannot_edit_delete_or_reassign_others_adaptations():
    stored = [_g("g1", "da Ana", R_ANA), _g("g2", "da Bia", R_BIA)]
    edited = [{**stored[0], "adaptation": "Ana editou", "responsible": R_BIA},     # tentou passar a dela para a Bia
              {**stored[1], "adaptation": "Ana mexeu na da Bia"}]
    out = merge_adaptations(stored, edited, actor_from_user(ANA), DEFAULT)
    by_id = {g["id"]: g for g in out}
    assert by_id["g1"]["adaptation"] == "Ana editou" and by_id["g1"]["responsible"] == R_ANA   # edita a dela, não troca o dono
    assert by_id["g2"] == stored[1]                                                           # a da Bia fica intacta
    assert {g["id"] for g in merge_adaptations(stored, [], actor_from_user(ANA), DEFAULT)} == {"g2"}  # apagar: só as dela


def test_only_coordination_changes_the_responsible():
    stored = [_g("g1", "da Ana", R_ANA)]
    out = merge_adaptations(stored, [{**stored[0], "responsible": {"teacher_id": "t-bia"}}], actor_from_user(COORD), DEFAULT)
    assert out[0]["responsible"] == {"teacher_id": "t-bia"}      # o nome é preenchido depois, no repositório
    assert merge_adaptations(stored, [], actor_from_user(COORD), DEFAULT) == []  # coordenação também apaga


def test_ownership_rules():
    assert owns(R_ANA, actor_from_user(ANA)) and not owns(R_ANA, actor_from_user(BIA))
    assert owns(R_ANA, actor_from_user(COORD)) and owns(None, actor_from_user(BIA))   # sem responsável: dado antigo, todos
    assert own_responsible(actor_from_user(COORD)) is None
    assert normalize_adaptations([{"adaptation": "a", "actions": ["x"], "responsible": R_ANA}])[0]["responsible"] == R_ANA


class Repo:
    def __init__(self, cards):
        self.cards, self.updated = cards, None

    async def list_by_student(self, sid):
        return self.cards

    async def get(self, cid):
        return next((c for c in self.cards if c["id"] == cid), None)

    async def update(self, cid, data):
        self.updated = data
        return {**await self.get(cid), **data}

    async def sync_skill_score(self, *a):
        return None


def _card(i, resp):
    return {"id": i, "student_id": "s1", "skill_id": None, "status": "todo", "title": i,
            "responsible_teacher_id": resp and resp["teacher_id"], "responsible_user_id": resp and resp["user_id"],
            "responsible_name": resp and resp["name"]}


CARDS = [_card("a", R_ANA), _card("b", R_BIA), _card("legacy", None)]


def test_each_teacher_sees_only_their_cards_and_coordination_sees_all():
    ids = lambda u: [c["id"] for c in asyncio.run(ListKanbanCardsUseCase(Repo(CARDS)).execute("s1", u)).value]  # noqa: E731
    assert ids(ANA) == ["a", "legacy"] and ids(BIA) == ["b", "legacy"]
    assert ids(COORD) == ["a", "b", "legacy"]


def test_teacher_cannot_update_someone_elses_card():
    repo = Repo(CARDS)
    res = asyncio.run(UpdateKanbanCardUseCase(repo).execute("b", {"daily_log": "oi"}, ANA))
    assert res.is_not_found and repo.updated is None
    assert asyncio.run(UpdateKanbanCardUseCase(repo).execute("a", {"daily_log": "oi"}, ANA)).is_ok
    assert asyncio.run(UpdateKanbanCardUseCase(repo).execute("b", {"daily_log": "ok"}, COORD)).is_ok

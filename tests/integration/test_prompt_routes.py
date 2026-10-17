"""Prompts de IA: só administrador e coordenação veem, editam, ativam ou excluem (todos os escopos), sem banco real."""
import pytest
from fastapi.testclient import TestClient

from core.constants.prompt_defaults import ALL_SCOPES, PROMPT_REGISTRY
from core.kernel.result import Result
from main import app

ADMIN = {"user_id": "a", "username": "admin@x", "full_name": "Admin", "role": "admin", "is_active": True}


class FakeUseCase:
    """Faz o token de teste virar um usuário com o papel desejado (a dependência real é require_roles)."""
    def __init__(self, role):
        self.role = role

    async def execute(self, token):
        return Result.ok({**ADMIN, "role": self.role})


class FakePromptRepo:
    def __init__(self):
        self.created = []

    async def get_active(self, scope):
        return {"id": f"__default_{scope}__", "scope": scope, "name": f"{scope} [base]", "content": "texto", "is_base": True, "updated_at": None}

    async def list_all(self, scope):
        return [await self.get_active(scope)]

    async def create(self, scope, name, description, content):
        self.created.append((scope, name))
        return {"id": "p1", "scope": scope, "name": name, "content": content}

    async def update(self, prompt_id, name, description, content):
        return {"id": prompt_id, "name": name, "content": content}

    async def activate(self, scope, prompt_id):
        return {"id": prompt_id, "scope": scope}

    async def deactivate(self, scope):
        return await self.get_active(scope)

    async def reset_to_default(self, scope):
        return await self.get_active(scope)

    async def delete(self, prompt_id):
        return True


def _client(role):
    app.container.validate_token_use_case.override(FakeUseCase(role))
    app.container.prompt_repository.override(FakePromptRepo())
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset():
    yield
    app.container.validate_token_use_case.reset_override()
    app.container.prompt_repository.reset_override()


AUTH = {"Authorization": "Bearer teste"}
CALLS = [
    ("get", "/prompts", None),
    ("get", "/prompts/diary_audio", None),
    ("get", "/prompts/diary_audio/active", None),
    ("post", "/prompts/diary_audio", {"name": "n", "content": "c"}),
    ("put", "/prompts/diary_audio/p1", {"name": "n", "content": "c"}),
    ("post", "/prompts/diary_audio/p1/activate", None),
    ("post", "/prompts/diary_audio/deactivate", None),
    ("post", "/prompts/diary_audio/reset", None),
    ("delete", "/prompts/diary_audio/p1", None),
]


@pytest.mark.parametrize("role", ["professor", "viewer", "secretaria", "parent", "therapist"])
@pytest.mark.parametrize("method,url,body", CALLS)
def test_other_roles_cannot_see_or_change_any_prompt(role, method, url, body):
    with _client(role) as c:
        r = getattr(c, method)(url, headers=AUTH, **({"json": body} if body is not None else {}))
    assert r.status_code == 403, (role, method, url)


@pytest.mark.parametrize("role", ["admin", "coordenacao"])
@pytest.mark.parametrize("method,url,body", CALLS)
def test_admin_and_coordination_can_manage_prompts(role, method, url, body):
    with _client(role) as c:
        r = getattr(c, method)(url, headers=AUTH, **({"json": body} if body is not None else {}))
    assert r.status_code in (200, 201, 204), (method, url, r.status_code)


def test_admin_lists_every_scope_with_metadata():
    with _client("admin") as c:
        data = c.get("/prompts", headers=AUTH).json()
    assert [d["scope"] for d in data] == list(ALL_SCOPES)
    assert all(d["label"] and d["description"] for d in data)
    assert next(d for d in data if d["scope"] == "diary_audio")["json_output"] is True


def test_unknown_scope_is_rejected():
    with _client("admin") as c:
        assert c.get("/prompts/nao_existe", headers=AUTH).status_code == 400


def test_registry_defaults_are_consistent():
    for scope, meta in PROMPT_REGISTRY.items():
        assert len(scope) <= 32, scope  # coluna ai_prompts.scope é String(32)
        if meta["default"] is not None:
            assert meta["default"].strip(), scope
        for ph in meta["placeholders"]:
            assert ph in meta["default"], (scope, ph)
    # o prompt do áudio deve pedir transcrição fiel, não resumo
    assert "NÃO um resumo" in PROMPT_REGISTRY["diary_audio"]["default"] or "NÃO condense" in PROMPT_REGISTRY["diary_audio"]["default"]

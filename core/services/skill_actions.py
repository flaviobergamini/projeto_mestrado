"""Ações práticas de uma habilidade: uma lista de conjuntos {action, adaptation, justification}.

Cada conjunto vira um card no Kanban e tem a SUA adaptação e justificativa. O campo `actions` do plano guarda essa lista em JSON; planos antigos guardavam
um texto com uma ação por linha, e continuam sendo lidos (cada linha vira uma ação sem adaptação)."""
import json
import uuid
from typing import Any, Optional


def _clean(item: Any) -> Optional[dict]:
    if hasattr(item, "model_dump"):
        item = item.model_dump()
    if isinstance(item, str):
        item = {"action": item, "adaptation": "", "justification": ""}
    if not isinstance(item, dict):
        return None
    action = str(item.get("action") or "").strip().lstrip("-•*0123456789.) ").strip()
    if not action:
        return None
    return {
        "id": str(item.get("id") or "").strip()[:64],
        "action": action[:500],
        "adaptation": str(item.get("adaptation") or "").strip()[:2000],
        "justification": str(item.get("justification") or "").strip()[:2000],
    }


def normalize_actions(value: Any) -> list[dict]:
    """Aceita lista de objetos/strings, JSON ou texto antigo (uma ação por linha)."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                value = parsed
            else:
                value = text.splitlines()
        except Exception:
            value = text.splitlines()
    return [c for c in (_clean(i) for i in value) if c]


def with_ids(items: list[dict]) -> list[dict]:
    """Garante um id estável por conjunto: é ele (e não o título) que liga o conjunto ao card do Kanban."""
    seen: set[str] = set()
    out = []
    for it in items:
        i = it.get("id") or ""
        if not i or i in seen:
            i = str(uuid.uuid4())
        seen.add(i)
        out.append({**it, "id": i})
    return out


def dump_actions(value: Any) -> Optional[str]:
    items = with_ids(normalize_actions(value))
    return json.dumps(items, ensure_ascii=False) if items else None


def actions_as_text(value: Any) -> str:
    """Texto para prompts: '- ação (adaptação: ...)'."""
    lines = []
    for it in normalize_actions(value):
        extra = [f"{k}: {it[f]}" for k, f in (("adaptação", "adaptation"), ("justificativa", "justification")) if it[f]]
        lines.append(f"- {it['action']}" + (f" ({'; '.join(extra)})" if extra else ""))
    return "\n".join(lines)

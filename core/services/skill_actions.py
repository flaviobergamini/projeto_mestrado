"""Ações práticas de uma habilidade: uma lista de {action, adaptation}.

Cada ação tem a SUA adaptação. O campo `actions` do plano guarda essa lista em JSON; planos antigos guardavam
um texto com uma ação por linha, e continuam sendo lidos (cada linha vira uma ação sem adaptação)."""
import json
from typing import Any, Optional


def _clean(item: Any) -> Optional[dict]:
    if hasattr(item, "model_dump"):
        item = item.model_dump()
    if isinstance(item, str):
        item = {"action": item, "adaptation": ""}
    if not isinstance(item, dict):
        return None
    action = str(item.get("action") or "").strip().lstrip("-•*0123456789.) ").strip()
    if not action:
        return None
    return {"action": action[:500], "adaptation": str(item.get("adaptation") or "").strip()[:2000]}


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


def dump_actions(value: Any) -> Optional[str]:
    items = normalize_actions(value)
    return json.dumps(items, ensure_ascii=False) if items else None


def actions_as_text(value: Any) -> str:
    """Texto para prompts: '- ação (adaptação: ...)'."""
    lines = []
    for it in normalize_actions(value):
        lines.append(f"- {it['action']}" + (f" (adaptação: {it['adaptation']})" if it["adaptation"] else ""))
    return "\n".join(lines)

"""Plano de uma habilidade: ADAPTAÇÕES, cada uma com a sua justificativa e uma ou mais AÇÕES PRÁTICAS.

    [{"id", "adaptation", "justification", "actions": [{"id", "action"}]}]

Cada ação vira um card no Kanban (o card fica ligado ao `id` da ação, não ao título; por isso editar o texto
atualiza o mesmo card). O JSON fica na coluna `student_skill_scores.actions`. Formatos antigos continuam sendo
lidos: itens planos {id, action, adaptation, justification} (cada um vira uma adaptação com uma ação) e o texto
com uma ação por linha."""
import json
import uuid
from typing import Any, Optional


def _text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _clean_action(item: Any) -> Optional[dict]:
    if hasattr(item, "model_dump"):
        item = item.model_dump()
    if isinstance(item, str):
        item = {"action": item}
    if not isinstance(item, dict):
        return None
    action = _text(item.get("action"), 600).lstrip("-•*0123456789.) ").strip()
    if not action:
        return None
    return {"id": _text(item.get("id"), 64), "action": action[:500]}


def _clean_group(item: Any) -> Optional[dict]:
    if hasattr(item, "model_dump"):
        item = item.model_dump()
    if isinstance(item, str):
        item = {"action": item}
    if not isinstance(item, dict):
        return None
    if "actions" in item:  # formato atual
        actions = [a for a in (_clean_action(x) for x in (item.get("actions") or [])) if a]
        group_id = _text(item.get("id"), 64)
    else:  # item plano antigo: o id dele era o id da ação (é a ele que o card do Kanban está ligado)
        action = _clean_action(item)
        actions = [action] if action else []
        group_id = ""
    adaptation, justification = _text(item.get("adaptation"), 2000), _text(item.get("justification"), 2000)
    if not actions and not adaptation and not justification:
        return None
    return {"id": group_id, "adaptation": adaptation, "justification": justification, "actions": actions}


def normalize_adaptations(value: Any) -> list[dict]:
    """Aceita lista (objetos/strings), JSON ou texto antigo (uma ação por linha)."""
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
            value = parsed if isinstance(parsed, list) else text.splitlines()
        except Exception:
            value = text.splitlines()
    return [g for g in (_clean_group(i) for i in value) if g]


def with_ids(groups: list[dict]) -> list[dict]:
    """Garante um id estável e único por adaptação e por ação."""
    seen: set[str] = set()

    def fresh(current: str) -> str:
        i = current if current and current not in seen else str(uuid.uuid4())
        seen.add(i)
        return i

    return [
        {**g, "id": fresh(g.get("id") or ""),
         "actions": [{**a, "id": fresh(a.get("id") or "")} for a in g.get("actions", [])]}
        for g in groups
    ]


def dump_adaptations(value: Any) -> Optional[str]:
    groups = with_ids(normalize_adaptations(value))
    return json.dumps(groups, ensure_ascii=False) if groups else None


def flatten_actions(groups: list[dict]) -> list[dict]:
    """Uma linha por ação, já com a adaptação e a justificativa dela (o que vira card no Kanban)."""
    return [
        {"id": a["id"], "action": a["action"], "adaptation": g["adaptation"], "justification": g["justification"],
         "adaptation_id": g["id"]}
        for g in groups for a in g["actions"]
    ]


def adaptations_as_text(value: Any) -> str:
    """Texto para prompts."""
    lines = []
    for g in normalize_adaptations(value):
        lines.append(f"- Adaptação: {g['adaptation'] or '(sem texto)'}"
                     + (f" | justificativa: {g['justification']}" if g["justification"] else ""))
        lines.extend(f"    * ação: {a['action']}" for a in g["actions"])
    return "\n".join(lines)

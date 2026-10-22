"""Plano de uma habilidade: ADAPTAÇÕES, cada uma com a sua justificativa e uma ou mais AÇÕES PRÁTICAS.

    [{"id", "adaptation", "justification", "responsible", "actions": [{"id", "action"}]}]

`responsible` = {teacher_id, user_id, name}: o professor responsável pela adaptação (e, portanto, pelas ações/cards).
Quem cria a adaptação é o responsável; só a coordenação (e o admin) troca o responsável. Cada professor edita
apenas as suas adaptações e vê as dos outros.

Cada ação vira um card no Kanban (o card fica ligado ao `id` da ação, não ao título; por isso editar o texto
atualiza o mesmo card). O JSON fica na coluna `student_skill_scores.actions`. Formatos antigos continuam sendo
lidos: itens planos {id, action, adaptation, justification} (cada um vira uma adaptação com uma ação) e o texto
com uma ação por linha."""
import json
import uuid
from typing import Any, Optional

COORDINATOR_ROLES = ("admin", "coordenacao")


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


def _clean_responsible(value: Any) -> Optional[dict]:
    if hasattr(value, "model_dump"):
        value = value.model_dump()
    if not isinstance(value, dict):
        return None
    out = {k: (str(value.get(k)).strip()[:255] if value.get(k) else None) for k in ("teacher_id", "user_id", "name")}
    return out if any(out.values()) else None


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
    return {"id": group_id, "adaptation": adaptation, "justification": justification,
            "responsible": _clean_responsible(item.get("responsible")), "actions": actions}


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
         "adaptation_id": g["id"], "responsible": g.get("responsible")}
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


# ───────────── autoria e permissões ─────────────

def actor_from_user(user: dict) -> dict:
    """Quem está agindo: o perfil do usuário logado (como vem de ValidateTokenUseCase)."""
    return {"role": user.get("role"), "user_id": user.get("user_id") or user.get("id"),
            "teacher_id": user.get("teacher_id"), "name": user.get("full_name") or user.get("username") or ""}


def is_coordinator(actor: dict) -> bool:
    return actor.get("role") in COORDINATOR_ROLES


def owns(responsible: Optional[dict], actor: dict) -> bool:
    """Pode editar/ver como dono? Coordenação sempre; professor só o que é dele. Sem responsável (dado antigo): todos."""
    if not responsible or is_coordinator(actor):
        return True
    teacher_id, user_id = responsible.get("teacher_id"), responsible.get("user_id")
    return bool((teacher_id and teacher_id == actor.get("teacher_id")) or (user_id and user_id == actor.get("user_id")))


def own_responsible(actor: dict) -> Optional[dict]:
    """Quem cria a adaptação como professor vira o responsável por ela."""
    if actor.get("role") != "professor":
        return None
    return {"teacher_id": actor.get("teacher_id"), "user_id": actor.get("user_id"), "name": actor.get("name")}


def card_responsible(card: dict) -> Optional[dict]:
    r = {"teacher_id": card.get("responsible_teacher_id"), "user_id": card.get("responsible_user_id"),
         "name": card.get("responsible_name")}
    return r if any(r.values()) else None


def merge_adaptations(stored: list[dict], incoming: list[dict], actor: dict, default: Optional[dict]) -> list[dict]:
    """Aplica a edição de `actor` sobre o plano guardado respeitando os responsáveis.

    * coordenação/admin: edita tudo e pode trocar o responsável (o `responsible` enviado vale);
    * professor: edita e apaga só as adaptações que são dele; as dos outros ficam exatamente como estão; o campo
      `responsible` enviado por ele é ignorado; adaptação nova passa a ser dele;
    * adaptação nova sem responsável definido: o professor que criou, ou o 'responsável 1' do aluno (`default`)."""
    stored_by_id = {g["id"]: g for g in stored if g["id"]}
    coord = is_coordinator(actor)
    result, seen = [], set()
    for g in incoming:
        old = stored_by_id.get(g["id"]) if g["id"] else None
        if old is None:
            responsible = (g.get("responsible") if coord else None) or own_responsible(actor) or default
            result.append({**g, "responsible": responsible})
            continue
        seen.add(old["id"])
        if coord:
            result.append({**g, "responsible": g.get("responsible") or old.get("responsible") or default})
        elif owns(old.get("responsible"), actor):
            result.append({**g, "responsible": old.get("responsible")})
        else:
            result.append(old)  # não é dele: nada muda
    if not coord:  # o professor não consegue apagar adaptações dos outros
        result.extend(g for g in stored if g["id"] not in seen and not owns(g.get("responsible"), actor))
    return result

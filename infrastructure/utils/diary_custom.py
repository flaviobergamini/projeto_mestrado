"""Respostas personalizadas do diário (guardadas em diary_entries.custom_answers)."""
import json
from typing import Optional


def parse_custom_answers(raw: Optional[str]) -> tuple[list[dict], dict]:
    """Retorna (lista de {key,label,answer}, {coluna_padrao: rotulo_alterado})."""
    if not raw:
        return [], {}
    try:
        data = json.loads(raw)
    except Exception:
        return [], {}
    custom = [c for c in (data.get("custom") or []) if isinstance(c, dict) and c.get("answer")]
    labels = data.get("labels") or {}
    return custom, labels if isinstance(labels, dict) else {}


def dump_custom_answers(custom: list[dict], labels: dict) -> Optional[str]:
    if not custom and not labels:
        return None
    return json.dumps({"custom": custom, "labels": labels}, ensure_ascii=False)

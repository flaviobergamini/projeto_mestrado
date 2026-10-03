"""Normalização, desanonimização e formatação do perfil funcional (JSON)."""
import json
import re
from typing import Any, Optional

from core.constants.functional_profile import DOMAINS


def _text_list(value: Any, limit: int = 8) -> list[str]:
    if isinstance(value, str):
        value = [v for v in re.split(r"[\n;]+", value)]
    if not isinstance(value, list):
        return []
    out = [str(v).strip() for v in value if str(v).strip()]
    return out[:limit]


def normalize_content(raw: Any) -> dict:
    """Garante o formato fixo: todos os domínios, nível 1-5 ou None, listas de texto."""
    raw = raw if isinstance(raw, dict) else {}
    by_key = {d.get("key"): d for d in raw.get("domains", []) if isinstance(d, dict)}
    domains = []
    for key, label in DOMAINS:
        d = by_key.get(key, {})
        level = d.get("level")
        try:
            level = int(level)
        except (TypeError, ValueError):
            level = None
        if level is not None and not 1 <= level <= 5:
            level = None
        domains.append({
            "key": key, "label": label, "level": level,
            "description": str(d.get("description") or "").strip()[:2000],
            "strengths": _text_list(d.get("strengths")),
            "needs": _text_list(d.get("needs")),
            "supports": _text_list(d.get("supports")),
        })
    return {
        "version": 1,
        "summary": str(raw.get("summary") or "").strip()[:4000],
        "domains": domains,
        "evidence": _text_list(raw.get("evidence"), 10),
    }


def parse_model_json(text: str) -> dict:
    """Extrai o objeto JSON da resposta do modelo (tolera cercas ``` e texto em volta)."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (text or "").strip(), flags=re.IGNORECASE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("A resposta da IA não contém um JSON.")
    return json.loads(cleaned[start:end + 1])


def map_strings(obj: Any, fn) -> Any:
    if isinstance(obj, str):
        return fn(obj)
    if isinstance(obj, list):
        return [map_strings(v, fn) for v in obj]
    if isinstance(obj, dict):
        return {k: map_strings(v, fn) for k, v in obj.items()}
    return obj


def average_level(content: dict) -> Optional[float]:
    levels = [d["level"] for d in content.get("domains", []) if d.get("level")]
    return round(sum(levels) / len(levels), 2) if levels else None


def format_functional_profile(meta: dict, content: dict, reanon) -> str:
    """Texto compacto para o contexto da IA. `reanon` troca nomes reais por IDs."""
    when = (meta.get("period_end") or meta.get("created_at") or "")[:10]
    origin = "elaborado com apoio de IA e revisado" if meta.get("origin") == "ai" else "registrado manualmente"
    lines = [
        f"=== PERFIL FUNCIONAL DO ALUNO (referência {when}; {origin}) ===",
        "Níveis de 1 a 5 (1 = precisa de apoio muito substancial; 5 = consolidado e independente); sem nível = sem evidência.",
    ]
    if content.get("summary"):
        lines.append("Resumo: " + reanon(content["summary"]))
    for d in content.get("domains", []):
        head = f"- {d['label']} (nível {d['level']}/5)" if d.get("level") else f"- {d['label']} (sem evidência suficiente)"
        parts = [head + (": " + reanon(d["description"]) if d.get("description") else "")]
        for key, title in (("strengths", "Pontos fortes"), ("needs", "Necessidades"), ("supports", "Apoios")):
            if d.get(key):
                parts.append(f"{title}: " + "; ".join(reanon(x) for x in d[key]))
        lines.append(" | ".join(parts))
    return "\n".join(lines)

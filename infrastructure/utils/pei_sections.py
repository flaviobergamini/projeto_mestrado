"""Quebra o texto de um PEI gerado em seções, uma por cabeçalho markdown —
usado para criar um card de Kanban por seção quando um PEI é gerado."""
import re

_HEADER_RE = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)

# Cards de execução não fazem sentido pra seções puramente burocráticas
# (identificação do aluno, assinaturas, base legal) — só as que descrevem
# algo que o professor de fato aplica em sala.
_SKIP_TITLE_KEYWORDS = ("identificação", "assinatura", "base legal", "vigência", "elaboração")


def parse_pei_sections(pei_text: str) -> list[dict]:
    """Retorna uma lista de {"title": str, "description": str}, uma por seção
    de nível 3 (###) do PEI — cai para nível 2 (##) se não houver nenhuma ###."""
    if not pei_text or not pei_text.strip():
        return []

    matches = list(_HEADER_RE.finditer(pei_text))
    h3_matches = [m for m in matches if m.group(1) == '###']
    use = h3_matches if h3_matches else matches
    if not use:
        return [{"title": "PEI Completo", "description": pei_text.strip()}]

    sections: list[dict] = []
    for i, m in enumerate(use):
        title = m.group(2).strip().lstrip('*').strip()
        if any(kw in title.lower() for kw in _SKIP_TITLE_KEYWORDS):
            continue
        start = m.end()
        end = use[i + 1].start() if i + 1 < len(use) else len(pei_text)
        body = pei_text[start:end].strip()
        if body:
            sections.append({"title": title, "description": body})
    return sections

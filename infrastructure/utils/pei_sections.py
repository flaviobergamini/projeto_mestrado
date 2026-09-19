"""Quebra o texto de um PEI gerado em seções, uma por cabeçalho markdown —
usado para criar um card de Kanban por seção quando um PEI é gerado."""
import re

_HEADER_RE = re.compile(r'^(#{2,3})\s+(.+)$', re.MULTILINE)

# Cards de execução não fazem sentido pra seções puramente burocráticas
# (identificação do aluno, assinaturas, base legal) — só as que descrevem
# algo que o professor de fato aplica em sala.
_SKIP_TITLE_KEYWORDS = ("identificação", "assinatura", "base legal", "vigência", "elaboração")


# Seções de objetivos viram um card por item (item de lista de primeiro nível),
# pra cada objetivo ser acompanhado/arrastado individualmente no Kanban.
_SPLIT_TITLE_KEYWORDS = ("objetivo",)
_ITEM_RE = re.compile(r'^(?:[-*•]|\d+[.)])\s+(.+)$')
_TITLE_MAX = 80


def _split_items(section_title: str, body: str) -> list[dict]:
    items: list[list[str]] = []
    for line in body.splitlines():
        m = _ITEM_RE.match(line)  # sem indentação => item de primeiro nível
        if m:
            items.append([m.group(1).strip()])
        elif items and line.strip():
            items[-1].append(line.strip())
    if len(items) < 2:
        return []
    out = []
    for lines in items:
        head = re.sub(r'[*_`]+', '', lines[0]).strip()
        short = head if len(head) <= _TITLE_MAX else head[:_TITLE_MAX].rsplit(' ', 1)[0] + '…'
        out.append({"title": f"{section_title}: {short}", "description": "\n".join(lines)})
    return out


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
        if not body:
            continue
        if any(kw in title.lower() for kw in _SPLIT_TITLE_KEYWORDS):
            split = _split_items(title, body)
            if split:
                sections.extend(split)
                continue
        sections.append({"title": title, "description": body})
    return sections

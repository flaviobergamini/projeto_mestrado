from infrastructure.utils.pei_sections import parse_pei_sections


def _titles(text):
    return [s["title"] for s in parse_pei_sections(text)]


def test_markdown_h3_headers():
    text = "## PEI\n### 1. Identificação\nx\n### 2. Perfil Funcional\ny\n### 4. Estratégias\nz\n"
    assert _titles(text) == ["2. Perfil Funcional", "4. Estratégias"]  # identificação é pulada


def test_bold_numbered_headers_are_recognized():
    body = "\n".join(f"**{n}. Seção {n}**\n\nTexto da seção {n}.\n" for n in range(1, 6))
    text = "## Plano Educacional Individualizado (PEI)\n\n" + body
    titles = _titles(text)
    assert titles == [f"{n}. Seção {n}" for n in range(1, 6)]


def test_numbered_list_items_in_body_are_not_headers():
    text = "### 2. Perfil\n1. item um\n2. item dois\n3. item três\n### 4. Estratégias\ntexto\n"
    assert _titles(text) == ["2. Perfil", "4. Estratégias"]


def test_objectives_are_split_per_item_also_in_bold_format():
    text = ("**1. Identificação**\nx\n**2. Perfil**\ny\n**3. Objetivos Educacionais**\n"
            "- Comunicar-se com colegas\n- Reduzir crises\n**4. Estratégias**\nz\n")
    titles = _titles(text)
    assert any(t.startswith("3. Objetivos Educacionais: Comunicar-se") for t in titles)
    assert any(t.startswith("3. Objetivos Educacionais: Reduzir crises") for t in titles)


def test_no_headers_returns_single_card():
    assert _titles("texto solto sem cabeçalhos") == ["PEI Completo"]

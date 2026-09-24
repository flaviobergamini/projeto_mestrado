from infrastructure.utils.llm_guards import has_degenerate_output, collapse_padding, MAX_PLAUSIBLE_CHARS


def test_normal_text_and_table_are_ok():
    text = "### 6. Adaptações\n\n| A | B |\n| :--- | :--- |\n| x | y |\n" + "   * item aninhado\n"
    assert not has_degenerate_output(text)


def test_detects_whitespace_loop():
    assert has_degenerate_output("| Componente | " + " " * 500 + "\n")


def test_detects_dash_loop_in_table_separator():
    assert has_degenerate_output("| " + "-" * 300 + " |")


def test_detects_absurdly_long_output():
    assert has_degenerate_output("palavra " * (MAX_PLAUSIBLE_CHARS // 4))


def test_empty_is_not_degenerate():
    assert not has_degenerate_output("")


def test_collapse_padding_keeps_normal_indentation():
    assert collapse_padding("      * item") == "      * item"
    assert collapse_padding("a" + " " * 50 + "b") == "a b"

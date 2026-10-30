import importlib.util
from pathlib import Path

import core.kernel.container  # noqa: F401  (carrega o container primeiro: evita import circular de core.kernel)
from infrastructure.repositories.bncc_repository import _grade_number, _grade_label

_spec = importlib.util.spec_from_file_location(
    "m0043", Path(__file__).resolve().parents[2] / "alembic" / "versions" / "0043_bncc_skill_year_range.py")
m0043 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m0043)


def test_year_range_comes_from_the_code():
    assert m0043.year_range("EF15LP01", [2, 3], "fundamental") == (1, 5)
    assert m0043.year_range("EF35LP01", [3], "fundamental") == (3, 5)
    assert m0043.year_range("EF12LP01", [1], "fundamental") == (1, 2)
    assert m0043.year_range("EF45GE02MG", [4], "fundamental") == (4, 5)
    assert m0043.year_range("EF13GEMG", [1], "fundamental") == (1, 3)


def test_single_year_codes_and_odd_codes():
    assert m0043.year_range("EF05MA01", [5], "fundamental") == (5, 5)  # EF05 = só o 5º ano
    assert m0043.year_range("EF04MA3B", [4], "fundamental") == (4, 4)
    assert m0043.year_range("XYZ", [2, 4], "fundamental") == (2, 4)    # fora do padrão: anos em que já estava
    assert m0043.year_range("EI03EO01", [0], "infantil") == (0, 0)


def test_labels_and_grade_numbers():
    assert m0043.label("fundamental", 1, 5, "") == "1º ao 5º ano"
    assert m0043.label("fundamental", 5, 5, "") == "5º ano"
    assert _grade_label("fundamental", 3, 5) == "3º ao 5º ano"
    assert _grade_number("3º ano") == 3
    assert _grade_number("Infantil (4 anos a 5 anos e 11 meses)") == 0

from core.services.bncc_codes import etapa_of, years_from_code


def test_years_from_code():
    assert years_from_code("EF12LP01") == (1, 2)
    assert years_from_code("EF15AR01") == (1, 5)
    assert years_from_code("EF35EF01") == (3, 5)
    assert years_from_code("EF67EF01") == (6, 7)
    assert years_from_code("EF69LP01") == (6, 9)
    assert years_from_code("EF89EF01") == (8, 9)
    assert years_from_code("EF06MA01") == (6, 6)
    assert years_from_code("EF01LP01") == (1, 1)
    assert years_from_code(" ef69lp05 ") == (6, 9)


def test_codes_without_years_or_crossing_the_stages():
    assert years_from_code("EI03EO01") is None
    assert years_from_code("XYZ") is None
    assert years_from_code("EF59LP01") is None   # cruza o Fundamental I e o II
    assert years_from_code("") is None


def test_etapa():
    assert etapa_of("infantil", 0) == "infantil"
    assert etapa_of("fundamental", 1) == "fundamental1" and etapa_of("fundamental", 5) == "fundamental1"
    assert etapa_of("fundamental", 6) == "fundamental2" and etapa_of("fundamental", 9) == "fundamental2"

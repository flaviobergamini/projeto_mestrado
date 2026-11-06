"""Anos e etapa de uma habilidade BNCC a partir do código.

Códigos do Ensino Fundamental: EF + dois dígitos + componente + número. Os dois dígitos são o ano inicial e o final
(EF12 = 1º ao 2º, EF15 = 1º ao 5º, EF35 = 3º ao 5º, EF67 = 6º ao 7º, EF69 = 6º ao 9º, EF89 = 8º ao 9º); com zero no
primeiro dígito é um ano só (EF06 = 6º ano). Códigos da Educação Infantil (EI...) não têm anos."""
import re
from typing import Optional

CODE_YEARS = re.compile(r"^EF(\d)(\d)")
INFANTIL, FUNDAMENTAL_1, FUNDAMENTAL_2 = "infantil", "fundamental1", "fundamental2"
FUNDAMENTAL_1_YEARS = range(1, 6)
FUNDAMENTAL_2_YEARS = range(6, 10)


def years_from_code(code: str) -> Optional[tuple[int, int]]:
    """(ano inicial, ano final) do código, ou None quando o código não diz (ex.: Educação Infantil, código livre)."""
    m = CODE_YEARS.match((code or "").strip().upper())
    if not m:
        return None
    a, b = int(m.group(1)), int(m.group(2))
    if a == 0 and 1 <= b <= 9:
        return b, b
    if 1 <= a <= b <= 9 and not (a <= 5 < b):  # uma habilidade não cruza o Fundamental I e o II
        return a, b
    return None


def etapa_of(stage: str, year_from: int) -> str:
    """Etapa de ensino: infantil, fundamental1 (1º ao 5º) ou fundamental2 (6º ao 9º)."""
    if stage == "infantil":
        return INFANTIL
    return FUNDAMENTAL_1 if year_from in FUNDAMENTAL_1_YEARS else FUNDAMENTAL_2

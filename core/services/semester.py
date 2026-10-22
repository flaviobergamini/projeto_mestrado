"""Semestre letivo (calendário): 1º = janeiro a junho; 2º = julho a dezembro."""
from datetime import date, datetime
from typing import Optional


def semester_bounds(day: date) -> tuple[date, date]:
    """Primeiro e último dia do semestre em que `day` cai."""
    if day.month <= 6:
        return date(day.year, 1, 1), date(day.year, 6, 30)
    return date(day.year, 7, 1), date(day.year, 12, 31)


def same_semester(created_at: Optional[datetime | date | str], today: date) -> bool:
    if not created_at:
        return False
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    day = created_at.date() if isinstance(created_at, datetime) else created_at
    start, end = semester_bounds(today)
    return start <= day <= end

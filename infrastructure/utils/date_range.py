"""Combina as três janelas de data (diário escolar/familiar/terapia) que o chat
e a geração de PEI aceitam separadamente numa única janela, para passar à busca
RAG — que filtra só por data de diário, sem distinguir o tipo."""
from typing import Optional, Protocol


class HasDiaryDateRanges(Protocol):
    diary_date_from: Optional[str]
    diary_date_to: Optional[str]
    family_diary_date_from: Optional[str]
    family_diary_date_to: Optional[str]
    therapy_diary_date_from: Optional[str]
    therapy_diary_date_to: Optional[str]


def broadest_date_from(body: HasDiaryDateRanges) -> Optional[str]:
    starts = [d for d in (body.diary_date_from, body.family_diary_date_from, body.therapy_diary_date_from) if d]
    return min(starts) if starts else None


def broadest_date_to(body: HasDiaryDateRanges) -> Optional[str]:
    ends = [d for d in (body.diary_date_to, body.family_diary_date_to, body.therapy_diary_date_to) if d]
    return max(ends) if ends else None

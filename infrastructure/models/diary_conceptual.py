from pydantic import BaseModel
from typing import Optional


class DiaryConceptual(BaseModel):
    """
    Modelo conceitual de diário como texto único.
    Usado para registros diários que serão processados via RAG.
    """
    beneficiary_id: int
    custom_questions: Optional[dict] = None

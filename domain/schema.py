from pydantic import BaseModel
from typing import List


class RAGRequest(BaseModel):
    pergunta: str
    model: str
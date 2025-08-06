from pydantic import BaseModel
from typing import List


class RAGRequest(BaseModel):
    user_id: str
    pergunta: str
from fastapi import APIRouter
from domain.schema import RAGRequest
from infrastructure.services.deepseek_service import DeepseekService
from infrastructure.services.gpt_service import GptService

router = APIRouter()
agent = GptService() #DeepseekService()

@router.post("/rag")
def responder_pergunta_rag(payload: RAGRequest):
    resposta = agent.chat(payload.user_id, payload.pergunta)
    return {"resposta": resposta}
from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from typing import Optional

from core.kernel.container import Container
from api.dependencies import get_current_user
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.services.gemini_service import GeminiService

router = APIRouter(prefix="/chat", tags=["Chat"])

SYSTEM_INSTRUCTION = """Você é um assistente especializado em educação inclusiva para alunos com Transtorno do Espectro Autista (TEA).
Responda sempre em português do Brasil, de forma clara e profissional.
Use os dados do aluno fornecidos para contextualizar suas respostas.
Foque em estratégias pedagógicas, comportamentais e de comunicação adequadas ao perfil do aluno.
Se não souber algo, diga claramente. Não invente informações sobre o aluno."""


class SendMessageRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    message: str


class SendMessageResponse(BaseModel):
    session_id: str
    answer: str
    message_index: int


@router.post("/message", response_model=SendMessageResponse)
@inject
async def send_message(
    body: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
):
    """Send a message and receive an AI response with student context."""
    user_id = current_user.get("user_id", "")
    username = current_user.get("full_name") or current_user.get("username", "")
    role = current_user.get("role", "")

    # Get or create session
    session_id = body.session_id
    if session_id:
        session = await chat_repo.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
    else:
        # Build student_name for session
        context = await chat_repo.get_student_context(body.student_id)
        first_line = context.split("\n")[0] if context else ""
        student_name = first_line.replace("ALUNO: ", "").strip() if first_line.startswith("ALUNO:") else None
        new_session = await chat_repo.create_session(
            user_id=user_id,
            username=username,
            role=role,
            student_id=body.student_id,
            student_name=student_name,
        )
        session_id = new_session["id"]

    # Build prompt with student context
    student_context = await chat_repo.get_student_context(body.student_id)
    prompt = f"""Contexto do aluno:
{student_context}

Pergunta do usuário: {body.message}"""

    # Save user message
    user_msg = await chat_repo.add_message(
        session_id=session_id,
        role="user",
        content=body.message,
        user_id=user_id,
        username=username,
    )

    # Generate AI response
    try:
        answer = gemini.generate_text(prompt=prompt, system_instruction=SYSTEM_INSTRUCTION)
    except Exception as exc:
        answer = "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente."

    # Save assistant message
    assistant_msg = await chat_repo.add_message(
        session_id=session_id,
        role="assistant",
        content=answer,
    )

    return SendMessageResponse(
        session_id=session_id,
        answer=answer,
        message_index=assistant_msg["message_index"],
    )


@router.get("/sessions")
@inject
async def list_sessions(
    student_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
):
    """List chat sessions for the current user, optionally filtered by student."""
    user_id = current_user.get("user_id", "")
    return await chat_repo.list_sessions(user_id=user_id, student_id=student_id)


@router.get("/sessions/{session_id}/messages")
@inject
async def get_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
):
    """Get all messages for a chat session."""
    session = await chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
    return await chat_repo.list_messages(session_id=session_id)

from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from typing import Optional

from core.kernel.container import Container
from api.dependencies import get_current_user
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.rag_service import RagService

router = APIRouter(prefix="/chat", tags=["Chat"])


class SendMessageRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    message: str
    sources: Optional[list[str]] = None  # e.g. ["diary", "case_study"]


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
    rag: RagService = Depends(Provide[Container.rag_service]),
    prompt_repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
):
    """Send a message and receive an AI response with RAG-retrieved student context."""
    user_id = current_user.get("user_id", "")
    username = current_user.get("full_name") or current_user.get("username", "")
    role = current_user.get("role", "")

    # Get or create session
    session_id = body.session_id
    student_name = ""
    if session_id:
        session = await chat_repo.get_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
        student_name = session.get("student_name") or ""
    else:
        # Use static context briefly just to extract the student name
        static_ctx = await chat_repo.get_student_context(body.student_id)
        first_line = static_ctx.split("\n")[0] if static_ctx else ""
        student_name = first_line.replace("ALUNO: ", "").strip() if first_line.startswith("ALUNO:") else ""
        new_session = await chat_repo.create_session(
            user_id=user_id,
            username=username,
            role=role,
            student_id=body.student_id,
            student_name=student_name or None,
        )
        session_id = new_session["id"]

    # RAG: retrieve semantically relevant chunks for the user's question
    rag_context = await rag.build_rag_context(
        query=body.message,
        student_id=body.student_id,
        student_name=student_name,
        limit=5,
        sources=body.sources,
    )

    prompt = f"""{rag_context}

Pergunta: {body.message}"""

    # Save user message
    await chat_repo.add_message(
        session_id=session_id,
        role="user",
        content=body.message,
        user_id=user_id,
        username=username,
    )

    # Load active system prompt (custom or default)
    prompt_data = await prompt_repo.get_active("chat")
    system_instruction = prompt_data["content"]

    # Generate AI response
    try:
        answer = gemini.generate_text(prompt=prompt, system_instruction=system_instruction)
    except Exception:
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


@router.get("/sources-preview")
@inject
async def get_sources_preview(
    student_id: str = Query(...),
    current_user: dict = Depends(get_current_user),
    rag: RagService = Depends(Provide[Container.rag_service]),
):
    """Return the count of available RAG sources for a given student."""
    return await rag.get_sources_preview(student_id)


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

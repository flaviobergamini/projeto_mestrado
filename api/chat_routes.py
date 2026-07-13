from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from typing import Optional

from core.kernel.container import Container
from api.dependencies import get_current_user
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.rag_service import RagService
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize

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
    debug_prompt: str | None = None


@router.post("/message", response_model=SendMessageResponse)
@inject
async def send_message(
    body: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
    gemini: GeminiService = Depends(Provide[Container.gemini_service]),
    rag: RagService = Depends(Provide[Container.rag_service]),
    prompt_repo: PromptRepository = Depends(Provide[Container.prompt_repository]),
    usage_repo: AiUsageRepository = Depends(Provide[Container.ai_usage_repository]),
    anon_svc: AnonymizationService = Depends(Provide[Container.anonymization_service]),
):
    """Send a message and receive an AI response with anonymised RAG context."""
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
        new_session = await chat_repo.create_session(
            user_id=user_id,
            username=username,
            role=role,
            student_id=body.student_id,
            student_name=None,  # never store real name in session
        )
        session_id = new_session["id"]

    # Build anonymised student context (profile + school + teachers + recent diary)
    anon_context, deanon_map = await anon_svc.build_context(body.student_id)

    # RAG: semantically similar chunks (already anonymised — no PII in embeddings)
    rag_context = await rag.build_rag_context(
        query=body.message,
        student_id=body.student_id,
        limit=5,
        sources=body.sources,
    )

    prompt = f"""=== CONTEXTO DO ALUNO (ANONIMIZADO) ===
{anon_context}

=== REGISTROS SIMILARES (RAG) ===
{rag_context}

=== PERGUNTA ===
{body.message}"""

    # Save user message
    await chat_repo.add_message(
        session_id=session_id,
        role="user",
        content=body.message,
        user_id=user_id,
        username=username,
    )

    # Load active system prompt
    prompt_data = await prompt_repo.get_active("chat")
    system_instruction = prompt_data["content"]

    # Generate AI response (anonymised prompt → Gemini)
    try:
        raw_answer, usage = gemini.generate_text_tracked(
            prompt=prompt,
            system_instruction=system_instruction,
        )
        await usage_repo.log(
            model=usage.model,
            operation="chat_rag",
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
            total_tokens=usage.total_tokens,
            duration_ms=usage.duration_ms,
            user_id=user_id,
            username=username,
        )
    except Exception:
        raw_answer = "Desculpe, ocorreu um erro ao processar sua pergunta. Tente novamente."
        deanon_map = {}

    # De-anonymise: replace UUIDs in the response with real names
    answer = deanonymize(raw_answer, deanon_map)

    # Save assistant message (de-anonymised version for display)
    assistant_msg = await chat_repo.add_message(
        session_id=session_id,
        role="assistant",
        content=answer,
    )

    return SendMessageResponse(
        session_id=session_id,
        answer=answer,
        message_index=assistant_msg["message_index"],
        debug_prompt=prompt,
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

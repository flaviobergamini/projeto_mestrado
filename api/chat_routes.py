import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from dependency_injector.wiring import inject, Provide
from pydantic import BaseModel
from typing import Optional

from core.kernel.container import Container
from api.dependencies import get_current_user
from infrastructure.repositories.chat_repository import ChatRepository
from infrastructure.repositories.prompt_repository import PromptRepository
from infrastructure.repositories.ai_usage_repository import AiUsageRepository
from infrastructure.repositories.student_repository import StudentRepository
from infrastructure.services.gemini_service import GeminiService
from infrastructure.services.rag_service import RagService
from infrastructure.services.anonymization_service import AnonymizationService, deanonymize
from infrastructure.services.pdf_service import generate_chat_pdf

router = APIRouter(prefix="/chat", tags=["Chat"])


class SendMessageRequest(BaseModel):
    student_id: str
    session_id: Optional[str] = None
    message: str
    sources: Optional[list[str]] = None
    diary_date_from: Optional[str] = None  # YYYY-MM-DD — diário escolar
    diary_date_to: Optional[str] = None    # YYYY-MM-DD
    family_diary_date_from: Optional[str] = None
    family_diary_date_to: Optional[str] = None
    therapy_diary_date_from: Optional[str] = None
    therapy_diary_date_to: Optional[str] = None


class RenameSessionRequest(BaseModel):
    title: str


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
    student_repo: StudentRepository = Depends(Provide[Container.student_repository]),
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

    # Contexto anonimizado e busca RAG não dependem um do outro — cada um abre
    # sua própria sessão de DB, então rodar em paralelo corta o tempo de espera
    # ao invés de somar os dois.
    (anon_context, deanon_map), rag_context = await asyncio.gather(
        anon_svc.build_context(
            body.student_id,
            sources=body.sources,
            diary_date_from=body.diary_date_from,
            diary_date_to=body.diary_date_to,
            family_diary_date_from=body.family_diary_date_from,
            family_diary_date_to=body.family_diary_date_to,
            therapy_diary_date_from=body.therapy_diary_date_from,
            therapy_diary_date_to=body.therapy_diary_date_to,
        ),
        rag.build_rag_context(
            query=body.message,
            student_id=body.student_id,
            limit=5,
            sources=body.sources,
        ),
    )

    # Regra de anonimização embutida no código (não no prompt editável de Chat) —
    # mesmo fix aplicado na geração de PEI: sem instrução explícita pra copiar o ID
    # literalmente, o Gemini inventa um placeholder tipo "[Nome do Aluno]" em vez do
    # UUID, e a desanonimização (deanonymize()) não acha o que substituir na resposta.
    student_for_rule = await student_repo.get_by_id(body.student_id)
    anonymization_rule = (
        "DADOS DO ALUNO (ANONIMIZADOS) — regra obrigatória: os identificadores abaixo "
        "substituem o nome real do aluno e da escola (limitação técnica do sistema, não "
        "ausência de informação). Sempre que for se referir ao aluno ou à escola pelo nome "
        "na resposta, copie o identificador EXATAMENTE como fornecido abaixo, sem alterá-lo, "
        "sem tentar adivinhar o nome real e sem usar um placeholder genérico como "
        '"[Nome do Aluno]" ou "[Nome da Escola]":\n'
        f"- ID do aluno: {body.student_id}\n"
        f"- ID da escola: {(student_for_rule or {}).get('school_id') or '(não informado)'}"
    )

    prompt = f"""{anonymization_rule}

=== CONTEXTO DO ALUNO (ANONIMIZADO) ===
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
        # generate_text_tracked é uma chamada de rede síncrona e bloqueante —
        # rodar em thread separada evita travar o event loop inteiro (e,
        # com isso, todas as outras requisições) enquanto o Gemini responde
        # ou faz retry por rate limit.
        raw_answer, usage = await asyncio.to_thread(
            gemini.generate_text_tracked,
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


@router.patch("/sessions/{session_id}")
@inject
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
):
    """Rename a chat session."""
    updated = await chat_repo.rename_session(session_id, body.title)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
    return updated


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
):
    """Delete a chat session and all its messages."""
    deleted = await chat_repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")


@router.get("/sessions/{session_id}/pdf")
@inject
async def export_session_pdf(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    chat_repo: ChatRepository = Depends(Provide[Container.chat_repository]),
):
    """Export a chat session as a PDF file."""
    session = await chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sessão não encontrada")
    messages = await chat_repo.list_messages(session_id=session_id)
    title = session.get("title") or f"Chat {session.get('session_date', '')}"
    # síncrona/CPU-bound (ReportLab) — roda em thread separada pra não travar o event loop
    pdf_bytes = await asyncio.to_thread(generate_chat_pdf, messages=messages, title=title)
    filename = f"chat_{session_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

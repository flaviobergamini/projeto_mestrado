import uuid
from datetime import date, datetime
from typing import Optional
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from infrastructure.database_context.database import Database
from infrastructure.models.chat_session import ChatSession
from infrastructure.models.chat_message import ChatMessage
from infrastructure.models.diary_entry import DiaryEntry
from infrastructure.models.pdi import Pdi
from infrastructure.models.case_study_submission import CaseStudySubmission
from infrastructure.models.student import Student


class ChatRepository:
    def __init__(self, database: Database):
        self._db = database

    async def create_session(
        self,
        user_id: str,
        username: str,
        role: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        school_name: Optional[str] = None,
    ) -> dict:
        async with self._db.session() as session:
            obj = ChatSession(
                id=str(uuid.uuid4()),
                session_date=date.today(),
                created_by_user_id=user_id,
                created_by_username=username,
                created_by_role=role,
                student_id=student_id,
                student_name=student_name,
                school_name=school_name,
            )

            session.add(obj)

            await session.commit()

            await session.refresh(obj)

            return self._session_to_dict(obj)

    async def get_session(self, session_id: str) -> Optional[dict]:
        async with self._db.session() as session:
            obj = await session.get(ChatSession, session_id)

            if not obj:
                return None
            
            return self._session_to_dict(obj)

    async def list_sessions(self, user_id: str, student_id: Optional[str] = None) -> list[dict]:
        async with self._db.session() as session:
            q = select(ChatSession).where(ChatSession.created_by_user_id == user_id)

            if student_id:
                q = q.where(ChatSession.student_id == student_id)

            q = q.order_by(desc(ChatSession.created_at))

            result = await session.execute(q)

            return [self._session_to_dict(r) for r in result.scalars()]

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
    ) -> dict:
        async with self._db.session() as session:
            count_q = select(func.count()).where(ChatMessage.session_id == session_id)

            count_result = await session.execute(count_q)

            idx = count_result.scalar() or 0

            msg = ChatMessage(
                id=str(uuid.uuid4()),
                session_id=session_id,
                message_index=idx,
                role=role,
                content=content,
                user_id=user_id,
                username=username,
            )

            session.add(msg)

            await session.commit()

            await session.refresh(msg)

            return self._message_to_dict(msg)

    async def list_messages(self, session_id: str) -> list[dict]:
        async with self._db.session() as session:
            q = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.message_index)
            )

            result = await session.execute(q)

            return [self._message_to_dict(m) for m in result.scalars()]

    async def get_student_context(self, student_id: str) -> str:
        """Builds a context string from student data for AI prompts."""
        async with self._db.session() as session:
            student = await session.get(Student, student_id)

            if not student:
                return "Aluno não encontrado."

            lines = [
                f"ALUNO: {student.name}",
                f"Ano/Série: {student.grade or 'não informado'}",
                f"Turma: {student.class_name or 'não informada'}",
                f"Diagnóstico: {student.diagnosis or 'não informado'}",
                f"Data de nascimento: {student.birth_date or 'não informada'}",
                "",
            ]

            # Last 5 diary entries
            diary_q = (
                select(DiaryEntry)
                .where(DiaryEntry.student_id == student_id)
                .order_by(desc(DiaryEntry.diary_date))
                .limit(5)
            )

            diary_result = await session.execute(diary_q)

            diaries = diary_result.scalars().all()

            if diaries:
                lines.append("REGISTROS DO DIÁRIO (últimos 5):")
                for d in diaries:
                    lines.append(f"  Data: {d.diary_date}")
                    lines.append(f"  Presença: {d.presence or 'não informado'}")

                    if d.open_observation:
                        lines.append(f"  Observação: {d.open_observation}")

                    respostas = []
                    if d.teacher_attention:
                        respostas.append(f"atenção ao professor={d.teacher_attention}")
                    if d.activity_interest:
                        respostas.append(f"interesse nas atividades={d.activity_interest}")
                    if d.participated_in_play:
                        respostas.append(f"participou de brincadeiras={d.participated_in_play}")
                    if d.completed_activities:
                        respostas.append(f"completou atividades={d.completed_activities}")
                    if respostas:
                        lines.append(f"  Indicadores: {', '.join(respostas)}")

                    lines.append("")

            # Most recent PDI
            pdi_q = (
                select(Pdi)
                .where(Pdi.student_id == student_id)
                .order_by(desc(Pdi.updated_at))
                .limit(1)
            )

            pdi_result = await session.execute(pdi_q)
            pdi = pdi_result.scalar_one_or_none()

            if pdi:
                lines.append("PDI (PLANO DE DESENVOLVIMENTO INDIVIDUAL):")
                lines.append(f"  Professor responsável: {pdi.teacher_name or 'não informado'}")
                lines.append(f"  Criado em: {pdi.created_at}")
                lines.append("")

            # Most recent case study
            cs_q = (
                select(CaseStudySubmission)
                .where(CaseStudySubmission.student_id == student_id)
                .order_by(desc(CaseStudySubmission.submitted_at))
                .limit(1)
            )

            cs_result = await session.execute(cs_q)
            cs = cs_result.scalar_one_or_none()

            if cs and cs.answers:
                lines.append("ESTUDO DE CASO (mais recente):")

                answers = cs.answers or {}

                nivel = answers.get("nivelAutismo", "não informado")

                lines.append(f"  Nível do autismo: {nivel}")

                if answers.get("comportamentos"):
                    lines.append(f"  Comportamentos: {answers['comportamentos']}")
                if answers.get("habilidades"):
                    lines.append(f"  Habilidades: {answers['habilidades']}")
                if answers.get("necessidades"):
                    lines.append(f"  Necessidades: {answers['necessidades']}")
                if answers.get("estrategias"):
                    lines.append(f"  Estratégias: {answers['estrategias']}")
                    
                lines.append("")

            return "\n".join(lines)

    def _session_to_dict(self, obj: ChatSession) -> dict:
        return {
            "id": obj.id,
            "session_date": str(obj.session_date) if obj.session_date else None,
            "student_id": obj.student_id,
            "student_name": obj.student_name,
            "school_name": obj.school_name,
            "created_by_username": obj.created_by_username,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
            "updated_at": obj.updated_at.isoformat() if obj.updated_at else None,
        }

    def _message_to_dict(self, obj: ChatMessage) -> dict:
        return {
            "id": obj.id,
            "session_id": obj.session_id,
            "message_index": obj.message_index,
            "role": obj.role,
            "content": obj.content,
            "username": obj.username,
            "created_at": obj.created_at.isoformat() if obj.created_at else None,
        }

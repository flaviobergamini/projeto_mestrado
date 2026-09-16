from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from infrastructure.database_context.database import Base
from infrastructure.utils.encryption import EncryptedText

if TYPE_CHECKING:
    from infrastructure.models.chat_session import ChatSession
    from infrastructure.models.user_profile import UserProfile


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("chat_sessions.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False, index=True
    )
    message_index: Mapped[int] = mapped_column(Integer, nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(64), ForeignKey("user_profiles.id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(EncryptedText, nullable=True)
    sources: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    user: Mapped[Optional["UserProfile"]] = relationship("UserProfile", back_populates="chat_messages")

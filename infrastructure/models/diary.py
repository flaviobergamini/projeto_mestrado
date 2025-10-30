from sqlalchemy import ForeignKey, Integer, DateTime, String, Text, Date
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base
from sqlalchemy.orm import Mapped, relationship, mapped_column
from datetime import date, datetime
from typing import Optional


class Diary(Base):
    """
    Modelo para registro diário de acompanhamento de alunos com TEA.
    Preenchido diariamente pelos professores de apoio para monitorar:
    - Comportamento
    - Desempenho em atividades
    - Socialização
    - Situações de crise
    - Aspectos emocionais
    """
    __tablename__ = "diary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Relacionamentos
    beneficiary_id: Mapped[int] = mapped_column(
        ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False
    )

    # Data do registro
    diary_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Aspectos comportamentais
    behavior_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    behavior_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: 1=Muito difícil, 5=Excelente

    # Desempenho em atividades
    activity_performance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    activity_engagement: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: nível de engajamento
    completed_activities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Lista de atividades completadas

    # Socialização
    socialization_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    peer_interaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: qualidade das interações
    adult_interaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: qualidade das interações

    # Situações de crise
    crisis_occurred: Mapped[bool] = mapped_column(default=False, nullable=False)
    crisis_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crisis_trigger: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crisis_intervention: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    crisis_duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Estado emocional
    emotional_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # calmo, ansioso, irritado, feliz, etc.
    mood_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: 1=Muito negativo, 5=Muito positivo

    # Comunicação
    communication_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verbal_communication: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: nível
    non_verbal_communication: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: nível

    # Autonomia
    autonomy_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    self_care_skills: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: independência
    task_independence: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5: independência

    # Observações gerais e sugestões
    general_observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    teacher_suggestions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    adaptations_needed: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Conquistas e progressos
    achievements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    beneficiary = relationship("Beneficiary", back_populates="diaries")
    user = relationship("User", back_populates="diaries")

from sqlalchemy import Column, Integer, Text, DateTime, JSON, ForeignKey, String
from sqlalchemy.sql import func
from infrastructure.database_context.database import Base


class PEI(Base):
    __tablename__ = "pei"

    id = Column(Integer, primary_key=True, index=True)
    beneficiary_id = Column(Integer, ForeignKey("beneficiary.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String, nullable=False)

    # JSON com todos os dados estruturados do PEI
    pei_data = Column(JSON, nullable=False)

    # Metadata adicional (ex: versão do prompt, modelo usado, etc)
    meta_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

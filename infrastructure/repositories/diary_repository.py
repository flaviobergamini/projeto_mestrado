from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.diary import Diary


class DiaryRepository:
    """
    Repositório para operações com registros diários de acompanhamento.
    Fornece métodos CRUD e consultas específicas para análise de padrões.
    """

    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, diary: Diary) -> Diary:
        """Adiciona um novo registro diário ao banco de dados"""
        async with self.database.session() as session:
            session.add(diary)
            await session.commit()
            await session.refresh(diary)
            return diary

    async def verify(self, entity: Diary) -> Diary | None:
        """Verifica se já existe um registro para o beneficiário na data específica"""
        async with self.database.session() as session:
            stmt = select(Diary).filter_by(
                beneficiary_id=entity.beneficiary_id,
                diary_date=entity.diary_date,
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def list_all(self) -> list[Diary]:
        """Lista todos os registros diários"""
        async with self.database.session() as session:
            result = await session.execute(select(Diary))
            return result.scalars().all()

    async def get_by_id(self, diary_id: int) -> Diary | None:
        """Busca um registro diário específico por ID"""
        async with self.database.session() as session:
            stmt = select(Diary).filter_by(id=diary_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_beneficiary(self, beneficiary_id: int) -> list[Diary]:
        """Lista todos os registros diários de um beneficiário específico"""
        async with self.database.session() as session:
            stmt = select(Diary).filter_by(beneficiary_id=beneficiary_id).order_by(Diary.diary_date.desc())
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_by_beneficiary_date_range(
        self, beneficiary_id: int, start_date, end_date
    ) -> list[Diary]:
        """Lista registros diários de um beneficiário em um período específico"""
        async with self.database.session() as session:
            stmt = (
                select(Diary)
                .filter_by(beneficiary_id=beneficiary_id)
                .filter(Diary.diary_date >= start_date)
                .filter(Diary.diary_date <= end_date)
                .order_by(Diary.diary_date.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_recent_entries(
        self, beneficiary_id: int, limit: int = 30
    ) -> list[Diary]:
        """Busca os registros mais recentes de um beneficiário (útil para análise de padrões)"""
        async with self.database.session() as session:
            stmt = (
                select(Diary)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(Diary.diary_date.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_crisis_entries(self, beneficiary_id: int) -> list[Diary]:
        """Busca todos os registros onde houve situação de crise"""
        async with self.database.session() as session:
            stmt = (
                select(Diary)
                .filter_by(beneficiary_id=beneficiary_id, crisis_occurred=True)
                .order_by(Diary.diary_date.desc())
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def update(self, diary_id: int, **kwargs) -> Diary | None:
        """Atualiza um registro diário existente"""
        try:
            async with self.database.session() as session:
                stmt = select(Diary).filter_by(id=diary_id)
                result = await session.execute(stmt)
                existing_diary = result.scalars().first()

                if not existing_diary:
                    return None

                for key, value in kwargs.items():
                    if hasattr(existing_diary, key):
                        setattr(existing_diary, key, value)

                await session.commit()
                await session.refresh(existing_diary)

                return existing_diary
        except Exception as e:
            raise e

    async def delete(self, diary_id: int) -> bool:
        """Remove um registro diário"""
        try:
            async with self.database.session() as session:
                stmt = select(Diary).filter_by(id=diary_id)
                result = await session.execute(stmt)
                diary = result.scalars().first()

                if not diary:
                    return False

                await session.delete(diary)
                await session.commit()
                return True
        except Exception as e:
            raise e

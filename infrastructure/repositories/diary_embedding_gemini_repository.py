import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini


class DiaryEmbeddingGeminiRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, diary_embedding: DiaryEmbeddingGemini) -> DiaryEmbeddingGemini:
        async with self.database.session() as session:
            session.add(diary_embedding)
            await session.commit()
            await session.refresh(diary_embedding)

            return diary_embedding

    async def search_similar_embeddings(self, query_embedding: list[float], limit: int = 5):
        embedding = np.array(query_embedding)

        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEmbeddingGemini)
                .order_by(DiaryEmbeddingGemini.embedding.cosine_distance(embedding))
                .limit(limit)
            )

            return result.scalars().all()

    async def search_similar_by_beneficiary(
        self, query_embedding: list[float], beneficiary_id: int, limit: int = 5
    ):
        """Busca embeddings similares apenas para um beneficiário específico"""
        embedding = np.array(query_embedding)

        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEmbeddingGemini)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(DiaryEmbeddingGemini.embedding.cosine_distance(embedding))
                .limit(limit)
            )

            return result.scalars().all()

    async def get_by_beneficiary(self, beneficiary_id: int):
        """Retorna todos os embeddings de um beneficiário"""
        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEmbeddingGemini).filter_by(beneficiary_id=beneficiary_id)
            )
            return result.scalars().all()

    async def delete_by_diary_id(self, diary_id: int) -> bool:
        """Remove embeddings vinculados a um diário específico"""
        try:
            async with self.database.session() as session:
                result = await session.execute(
                    select(DiaryEmbeddingGemini).filter_by(diary_id=diary_id)
                )
                embeddings = result.scalars().all()

                for embedding in embeddings:
                    await session.delete(embedding)

                await session.commit()
                return True
        except Exception as e:
            raise e
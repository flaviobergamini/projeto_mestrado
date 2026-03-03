import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.pei_embedding_gemini import PEIEmbeddingGemini


class PEIEmbeddingGeminiRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, pei_embedding: PEIEmbeddingGemini) -> PEIEmbeddingGemini:
        """Adiciona um novo embedding de PEI"""
        async with self.database.session() as session:
            session.add(pei_embedding)
            await session.commit()
            await session.refresh(pei_embedding)
            return pei_embedding

    async def search_similar_embeddings(self, query_embedding: list[float], limit: int = 5):
        """Busca embeddings similares em todos os PEIs"""
        embedding = np.array(query_embedding)

        async with self.database.session() as session:
            result = await session.execute(
                select(PEIEmbeddingGemini)
                .order_by(PEIEmbeddingGemini.embedding.cosine_distance(embedding))
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
                select(PEIEmbeddingGemini)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(PEIEmbeddingGemini.embedding.cosine_distance(embedding))
                .limit(limit)
            )
            return result.scalars().all()

    async def get_by_pei_id(self, pei_id: int):
        """Retorna todos os embeddings de um PEI específico"""
        async with self.database.session() as session:
            result = await session.execute(
                select(PEIEmbeddingGemini).filter_by(pei_id=pei_id)
            )
            return result.scalars().all()

    async def get_by_beneficiary(self, beneficiary_id: int):
        """Retorna todos os embeddings de um beneficiário"""
        async with self.database.session() as session:
            result = await session.execute(
                select(PEIEmbeddingGemini).filter_by(beneficiary_id=beneficiary_id)
            )
            return result.scalars().all()

    async def delete_by_pei_id(self, pei_id: int) -> bool:
        """Remove todos os embeddings de um PEI específico"""
        try:
            async with self.database.session() as session:
                result = await session.execute(
                    select(PEIEmbeddingGemini).filter_by(pei_id=pei_id)
                )
                embeddings = result.scalars().all()

                for embedding in embeddings:
                    await session.delete(embedding)

                await session.commit()
                return True
        except Exception as e:
            raise e

    async def delete_by_beneficiary(self, beneficiary_id: int) -> bool:
        """Remove todos os embeddings de um beneficiário específico"""
        try:
            async with self.database.session() as session:
                result = await session.execute(
                    select(PEIEmbeddingGemini).filter_by(beneficiary_id=beneficiary_id)
                )
                embeddings = result.scalars().all()

                for embedding in embeddings:
                    await session.delete(embedding)

                await session.commit()
                return True
        except Exception as e:
            raise e

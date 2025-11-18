import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.institution_embedding_gemini import InstitutionEmbeddingGemini


class InstitutionEmbeddingGeminiRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, institution_embedding: InstitutionEmbeddingGemini) -> InstitutionEmbeddingGemini:
        async with self.database.session() as session:
            session.add(institution_embedding)
            await session.commit()
            await session.refresh(institution_embedding)

            return institution_embedding

    async def search_similar_embeddings(self, query_embedding: list[float], limit: int = 5):
        """Busca embeddings similares em todas as instituições"""
        embedding = np.array(query_embedding)

        async with self.database.session() as session:
            result = await session.execute(
                select(InstitutionEmbeddingGemini)
                .order_by(InstitutionEmbeddingGemini.embedding.cosine_distance(embedding))
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
                select(InstitutionEmbeddingGemini)
                .filter_by(beneficiary_id=beneficiary_id)
                .order_by(InstitutionEmbeddingGemini.embedding.cosine_distance(embedding))
                .limit(limit)
            )

            return result.scalars().all()

    async def get_by_beneficiary(self, beneficiary_id: int):
        """Retorna todos os embeddings de um beneficiário"""
        async with self.database.session() as session:
            result = await session.execute(
                select(InstitutionEmbeddingGemini).filter_by(beneficiary_id=beneficiary_id)
            )
            return result.scalars().all()

    async def delete_by_beneficiary(self, beneficiary_id: int) -> bool:
        """Remove todos os embeddings de um beneficiário específico"""
        try:
            async with self.database.session() as session:
                result = await session.execute(
                    select(InstitutionEmbeddingGemini).filter_by(beneficiary_id=beneficiary_id)
                )
                embeddings = result.scalars().all()

                for embedding in embeddings:
                    await session.delete(embedding)

                await session.commit()
                return True
        except Exception as e:
            raise e

import numpy as np
from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.diary_embedding_groq import DiaryEmbeddingGroq


class DiaryEmbeddingGroqRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, diary_embedding: DiaryEmbeddingGroq) -> DiaryEmbeddingGroq:
        async with self.database.session() as session:
            session.add(diary_embedding)
            await session.commit()
            await session.refresh(diary_embedding)
            
            return diary_embedding
        
    async def search_similar_embeddings(self, query_embedding: list[float], limit: int = 5):
        embedding = np.array(query_embedding)

        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEmbeddingGroq)
                .order_by(DiaryEmbeddingGroq.embedding.cosine_distance(embedding))
                .limit(limit)
            )

            return result.scalars().all()
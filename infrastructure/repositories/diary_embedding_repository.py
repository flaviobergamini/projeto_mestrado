from sqlalchemy import select
from infrastructure.database_context.database import Database
from infrastructure.models.diary_embedding import DiaryEmbedding


class DiaryEmpeddingRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def add(self, diary_embedding: DiaryEmbedding) -> DiaryEmbedding:
        async with self.database.session() as session:
            session.add(diary_embedding)
            await session.commit()
            await session.refresh(diary_embedding)
            
            return diary_embedding
        
    async def search_embeddings(self, query_embedding: list[float], limit: int = 5):
        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEmbedding)
                .order_by(DiaryEmbedding.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )

            return result.scalars().all()
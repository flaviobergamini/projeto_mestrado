from contextlib import asynccontextmanager
from typing import AsyncIterator
from core.config import settings

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Database:
    def __init__(self, url: str | None = None) -> None:
        self.url = url or settings.DATABASE_URL
        if not self.url:
            raise RuntimeError("DATABASE_URL não está definido")
        
        self.engine = create_async_engine(
            self.url,
            pool_pre_ping=True,
            # Recicla conexões ociosas depois de 30min — o pooler do Supabase às
            # vezes derruba conexões silenciosamente em segundo plano; sem isso,
            # a próxima query nessa conexão falha direto na abertura (visto ao
            # vivo: asyncpg.connect() falhando com um 500 em /chat/sources-preview,
            # não um timeout de espera pelo pool — indicando conexão obsoleta, não
            # esgotamento do pool em si).
            pool_recycle=1800,
            connect_args={"statement_cache_size": 0},
            execution_options={"prepared_statement_cache_size": 0},
        )
        self.session_factory = async_sessionmaker(
            self.engine, expire_on_commit=False
        )

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

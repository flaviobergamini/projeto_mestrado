from infrastructure.database_context.database import Database
from infrastructure.models.app_setting import AppSetting


class AppSettingsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def get(self, key: str, default: dict) -> dict:
        """Valor salvo mesclado sobre o padrão (chaves novas do padrão aparecem mesmo em configurações antigas)."""
        async with self.database.session() as session:
            row = await session.get(AppSetting, key)
        return {**default, **(row.value if row else {})}

    async def set(self, key: str, value: dict) -> dict:
        async with self.database.session() as session:
            row = await session.get(AppSetting, key)
            if row:
                row.value = value
            else:
                session.add(AppSetting(key=key, value=value))
            await session.commit()
        return value

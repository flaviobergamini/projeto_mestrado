"""Define a senha local de um usuário (login sem Cognito, sem regras de senha).

Uso:
  python set_password.py roanita roa1234           # por e-mail ou nome de usuário
  python set_password.py --all-missing roa1234     # todos os usuários que ainda não têm senha local
"""
import asyncio
import sys
from sqlalchemy import select
from core.services.jwt_service import JwtService
from infrastructure.database_context.database import Database
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.models.user_profile import UserProfile


async def main():
    args = sys.argv[1:]
    repo = UserRepository(Database())
    jwt = JwtService()
    if len(args) == 2 and args[0] == "--all-missing":
        async with repo.database.session() as s:
            ids = (await s.execute(select(UserProfile.id).where(
                UserProfile.password_hash.is_(None), UserProfile.deleted == False))).scalars().all()
        h = jwt.hash_password(args[1])
        for uid in ids:
            await repo.set_password_hash(uid, h)
        print(f"{len(ids)} usuário(s) sem senha receberam a senha informada.")
    elif len(args) == 2:
        user = await repo.find_by_login(args[0])
        if not user:
            sys.exit("Usuário não encontrado")
        await repo.set_password_hash(user["id"], jwt.hash_password(args[1]))
        print(f"Senha definida para {user['username']}")
    else:
        sys.exit(__doc__)

asyncio.run(main())

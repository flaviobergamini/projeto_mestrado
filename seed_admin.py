"""
Script de seed do administrador inicial.

Execução:
    python seed_admin.py

O script:
  1. Valida as variáveis de ambiente necessárias
  2. Cria o usuário no AWS Cognito (e confirma automaticamente sem e-mail)
  3. Insere o perfil em user_profiles com role = 'admin'

Se o admin já existir (Cognito ou banco), o script é idempotente
e apenas avisa sem lançar erro.

Variáveis necessárias no .env:
    ADMIN_EMAIL=admin@exemplo.com
    ADMIN_PASSWORD=SenhaForte@123
    ADMIN_FULL_NAME=Administrador      (opcional)
    COGNITO_USER_POOL_ID=...
    COGNITO_APP_CLIENT_ID=...
    COGNITO_REGION=...
    DATABASE_URL=...
"""

import asyncio
import uuid
import sys
import boto3
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.config import settings
from infrastructure.models.user_profile import UserProfile
from infrastructure.models import (  # noqa: F401 — garante que todos os models são registrados
    Municipality, School, Teacher, Student, TeacherStudentLink,
    DiaryEntry, Pdi, PdiTrimesterSubject, ChatSession, ChatMessage,
    CaseStudySubmission, SchoolRegistrationSubmission, ObjectStorageFile,
    DiaryEmbeddingGemini, PdiEmbeddingGemini,
)


# ------------------------------------------------------------------ #
# Helpers Cognito                                                      #
# ------------------------------------------------------------------ #

def _secret_hash(username: str) -> str:
    if not settings.COGNITO_APP_CLIENT_SECRET:
        return None
    message = username + settings.COGNITO_APP_CLIENT_ID
    secret = settings.COGNITO_APP_CLIENT_SECRET.encode("utf-8")
    digest = hmac.new(secret, message.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def _cognito_client():
    return boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)


def create_cognito_admin(email: str, password: str, full_name: str) -> str:
    """
    Cria o usuário no Cognito e confirma automaticamente via admin API
    (sem precisar de código por e-mail).
    Retorna o cognito_sub (UUID do usuário).
    """
    client = _cognito_client()

    # 1. sign_up
    kwargs = dict(
        ClientId=settings.COGNITO_APP_CLIENT_ID,
        Username=email,
        Password=password,
        UserAttributes=[
            {"Name": "email", "Value": email},
            {"Name": "name", "Value": full_name},
        ],
    )
    secret = _secret_hash(email)
    if secret:
        kwargs["SecretHash"] = secret

    try:
        response = client.sign_up(**kwargs)
        cognito_sub = response["UserSub"]
        print(f"  [Cognito] Usuário criado: {email} (sub={cognito_sub})")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "UsernameExistsException":
            # Busca o sub do usuário já existente
            user = client.admin_get_user(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=email,
            )
            cognito_sub = next(
                (a["Value"] for a in user["UserAttributes"] if a["Name"] == "sub"),
                None,
            )
            print(f"  [Cognito] Usuário já existe: {email} (sub={cognito_sub})")
        else:
            raise

    # 2. Confirma automaticamente via admin (sem código de e-mail)
    try:
        client.admin_confirm_sign_up(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
        print(f"  [Cognito] E-mail confirmado automaticamente.")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NotAuthorizedException":
            # Já estava confirmado
            print(f"  [Cognito] Usuário já estava confirmado.")
        else:
            raise

    return cognito_sub


# ------------------------------------------------------------------ #
# Helpers banco de dados                                               #
# ------------------------------------------------------------------ #

async def create_db_admin(cognito_sub: str, email: str, full_name: str):
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        # Verifica se já existe
        result = await session.execute(
            select(UserProfile).where(UserProfile.id == cognito_sub)
        )
        existing = result.scalars().first()

        if existing:
            print(f"  [DB] Perfil admin já existe (id={cognito_sub})")
            await engine.dispose()
            return

        user = UserProfile(
            id=cognito_sub,
            username=email,
            full_name=full_name,
            role="admin",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"  [DB] Perfil admin inserido em user_profiles (id={cognito_sub})")

    await engine.dispose()


# ------------------------------------------------------------------ #
# Validações                                                           #
# ------------------------------------------------------------------ #

def validate_env():
    errors = []
    if not settings.ADMIN_EMAIL:
        errors.append("ADMIN_EMAIL não definido no .env")
    if not settings.ADMIN_PASSWORD:
        errors.append("ADMIN_PASSWORD não definido no .env")
    if not settings.COGNITO_USER_POOL_ID:
        errors.append("COGNITO_USER_POOL_ID não definido no .env")
    if not settings.COGNITO_APP_CLIENT_ID:
        errors.append("COGNITO_APP_CLIENT_ID não definido no .env")
    if not settings.DATABASE_URL:
        errors.append("DATABASE_URL não definido no .env")
    if errors:
        print("\n[ERRO] Variáveis de ambiente faltando:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)


# ------------------------------------------------------------------ #
# Entry point                                                          #
# ------------------------------------------------------------------ #

async def main():
    print("\n=== Seed: Admin inicial ===\n")
    validate_env()

    email     = settings.ADMIN_EMAIL
    password  = settings.ADMIN_PASSWORD
    full_name = settings.ADMIN_FULL_NAME

    print(f"E-mail  : {email}")
    print(f"Nome    : {full_name}")
    print(f"Role    : admin\n")

    print("[1/2] Criando usuário no Cognito...")
    cognito_sub = create_cognito_admin(email, password, full_name)

    print("\n[2/2] Criando perfil no banco de dados...")
    await create_db_admin(cognito_sub, email, full_name)

    print("\n✓ Admin criado com sucesso!")
    print(f"  Login: {email} / (senha definida no .env)\n")


if __name__ == "__main__":
    asyncio.run(main())

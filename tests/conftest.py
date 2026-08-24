"""Configuração compartilhada de testes.

Define variáveis de ambiente ANTES de qualquer módulo da aplicação ser
importado (pytest sempre carrega conftest.py antes de coletar os testes),
para que `core.config.settings` nunca veja valores ausentes/inválidos —
sem isso, o import de `infrastructure.utils.encryption` falharia (chave
Fernet ausente) e a criação do `Database` falharia (DATABASE_URL ausente).

Nenhum destes valores aponta para infraestrutura real: os testes de
integração sobrescrevem os providers do container de DI (repositórios,
serviços) antes de exercitar qualquer rota, então o "banco" e as
credenciais AWS abaixo nunca são efetivamente usados.
"""

import os

from cryptography.fernet import Fernet

os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("GEMINI_MODEL", "gemini-2.5-flash")
os.environ.setdefault("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
os.environ.setdefault("COGNITO_REGION", "us-east-1")
os.environ.setdefault("COGNITO_USER_POOL_ID", "test-pool-id")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "test-client-id")
os.environ.setdefault("COGNITO_APP_CLIENT_SECRET", "test-client-secret")

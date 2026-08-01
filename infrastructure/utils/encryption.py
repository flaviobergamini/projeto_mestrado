"""SQLAlchemy TypeDecorators that transparently encrypt/decrypt column values.

EncryptedText  — for String / Text columns
EncryptedJSON  — for JSON columns (dict / list)

Both handle legacy unencrypted values gracefully: if decryption fails the raw
value is returned as-is, so existing rows keep working without a data migration.

The Fernet cipher (AES-128-CBC + HMAC-SHA256) runs in C via OpenSSL through the
`cryptography` package and adds negligible overhead per row (~0.1 ms).
"""

import json
import logging
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Text, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

from core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — one Fernet instance per process, created once.
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.ENCRYPTION_KEY
        if not key:
            raise RuntimeError("ENCRYPTION_KEY is not configured in settings.")
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()


class EncryptedText(TypeDecorator):
    """Stores a string as Fernet-encrypted ciphertext in a Text column."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return encrypt(str(value))

    def process_result_value(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        try:
            return decrypt(value)
        except (InvalidToken, Exception):
            # Legacy plaintext row — return as-is
            return value


class EncryptedJSON(TypeDecorator):
    """Stores a dict/list as Fernet-encrypted JSON in a Text column."""

    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: Any) -> str | None:
        if value is None:
            return None
        return encrypt(json.dumps(value, ensure_ascii=False))

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return None
        try:
            plaintext = decrypt(value)
        except (InvalidToken, Exception):
            # Legacy plaintext JSON
            plaintext = value
        try:
            return json.loads(plaintext)
        except (json.JSONDecodeError, TypeError):
            return plaintext

from core.config import settings
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import secrets

class JwtService:
    def __init__(self):
        self.secret_key = settings.JWT_SECRET
        self.algorithm = "HS256"
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return self.pwd_context.verify(plain, hashed)

    def create_access_token(self, data: dict, expires_delta: int = 60):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict, expires_delta: int = 10080):  # 7 days
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_verification_token(self, data: dict, expires_delta: int = 1440):  # 24 hours
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire, "type": "verification"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_reset_token(self, data: dict, expires_delta: int = 60):  # 1 hour
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_delta)
        to_encode.update({"exp": expire, "type": "reset"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

    def get_user_id_from_token(self, token: str) -> str | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        return payload.get("sub")

    def get_role_from_token(self, token: str) -> str | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        return payload.get("role")

    def get_token_type(self, token: str) -> str | None:
        payload = self.decode_token(token)
        if not payload:
            return None
        return payload.get("type")

    def generate_secure_token(self) -> str:
        """Gera um token seguro aleatório"""
        return secrets.token_urlsafe(32)
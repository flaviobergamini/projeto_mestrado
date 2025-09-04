from core.config import settings
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

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
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str):
        try:
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except jwt.ExpiredSignatureError:
            return None
    
    def get_user_id_from_token(self, token: str) -> str | None:
        payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        if not payload:
            return None
        return payload.get("sub")
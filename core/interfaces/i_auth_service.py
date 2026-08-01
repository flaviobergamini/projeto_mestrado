from abc import ABC, abstractmethod
from typing import Optional


class IAuthService(ABC):

    @abstractmethod
    def admin_create_user(self, username: str, password: str, email: str, full_name: Optional[str]) -> str:
        """Cria usuário via API admin (já confirmado, sem código de verificação) e retorna o sub."""
        ...

    @abstractmethod
    def sign_up(self, username: str, password: str, email: str, full_name: Optional[str]) -> str:
        """Registra usuário e retorna o ID (sub) gerado."""
        ...

    @abstractmethod
    def confirm_sign_up(self, username: str, code: str) -> None:
        ...

    @abstractmethod
    def resend_confirmation_code(self, username: str) -> None:
        ...

    @abstractmethod
    def sign_in(self, username: str, password: str) -> dict:
        """Retorna dict com access_token, id_token, refresh_token, expires_in."""
        ...

    @abstractmethod
    def refresh_token(self, username: str, refresh_token: str) -> dict:
        """Retorna dict com access_token, id_token, expires_in."""
        ...

    @abstractmethod
    def forgot_password(self, username: str) -> None:
        ...

    @abstractmethod
    def confirm_forgot_password(self, username: str, code: str, new_password: str) -> None:
        ...

    @abstractmethod
    def get_username_from_token(self, access_token: str) -> str:
        """Valida o token e retorna o username. Lança AuthException se inválido."""
        ...

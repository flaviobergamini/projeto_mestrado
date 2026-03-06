from supabase import create_client, Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)


class SupabaseAuthService:
    def __init__(self):
        self.url = settings.SUPABASE_URL
        self.key = settings.SUPABASE_KEY

    def _client(self) -> Client:
        return create_client(self.url, self.key)

    def sign_up(self, email: str, password: str, name: str):
        return self._client().auth.sign_up({
            "email": email,
            "password": password,
            "options": {"data": {"name": name}}
        })

    def sign_in(self, email: str, password: str):
        return self._client().auth.sign_in_with_password({
            "email": email,
            "password": password
        })

    def reset_password_for_email(self, email: str):
        redirect_to = f"{settings.FRONTEND_URL}/auth/reset-password"
        return self._client().auth.reset_password_for_email(
            email, {"redirect_to": redirect_to}
        )

    def update_password(self, access_token: str, refresh_token: str, new_password: str):
        client = self._client()
        client.auth.set_session(access_token, refresh_token)
        return client.auth.update_user({"password": new_password})

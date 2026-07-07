import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "agents-buket")

# Signed URL validity in seconds (24 h — long enough for in-page display)
SIGNED_URL_EXPIRY = 86400


class StorageService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return self._client

    def upload(self, object_key: str, content: bytes, content_type: str) -> str:
        """Uploads bytes to Supabase Storage. Returns a signed URL valid for 24 h."""
        client = self._get_client()
        client.storage.from_(SUPABASE_BUCKET).upload(
            path=object_key,
            file=content,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        return self.create_signed_url(object_key) or self.public_url(object_key)

    def create_signed_url(self, object_key: str, expires_in: int = SIGNED_URL_EXPIRY) -> Optional[str]:
        """Returns a signed URL valid for `expires_in` seconds, or None on error."""
        try:
            client = self._get_client()
            response = client.storage.from_(SUPABASE_BUCKET).create_signed_url(
                path=object_key,
                expires_in=expires_in,
            )
            # Supabase Python client returns the URL directly as a string in newer versions,
            # or a dict with 'signedURL' / 'signedUrl' in older ones.
            if isinstance(response, str):
                return response
            if isinstance(response, dict):
                return response.get("signedURL") or response.get("signedUrl") or response.get("data", {}).get("signedUrl")
        except Exception:
            pass
        return None

    def delete(self, object_key: str) -> bool:
        try:
            client = self._get_client()
            client.storage.from_(SUPABASE_BUCKET).remove([object_key])
            return True
        except Exception:
            return False

    def public_url(self, object_key: str) -> str:
        return f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{object_key}"

    @property
    def bucket(self) -> str:
        return SUPABASE_BUCKET

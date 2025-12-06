from supabase import create_client, Client
from core.config import settings
from typing import Optional, Tuple, List
from datetime import datetime
import os
import uuid
import tempfile



class StorageService:
    """
    Serviço para gerenciar uploads, downloads e exclusões de arquivos no Supabase Storage.
    Compatível com a documentação oficial do SDK Python:
    https://supabase.com/docs/reference/python/storage-from-upload
    """

    def __init__(self):
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL e SUPABASE_KEY devem estar configuradas nas variáveis de ambiente."
            )

        # Cria cliente
        self.client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        self.bucket_name = settings.SUPABASE_BUCKET

    # ------------------------
    # Utilitários internos
    # ------------------------
    def _generate_unique_filename(self, original_filename: str, user_id: str) -> str:
        """
        Gera um caminho único para o arquivo dentro do bucket.
        Ex: user123/20250101_120000_abc123.png
        """
        file_extension = os.path.splitext(original_filename)[1]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{user_id}/{timestamp}_{unique_id}{file_extension}"

    # ------------------------
    # Upload de arquivo
    # ------------------------
    def upload_file(self, file_content: bytes, filename: str, user_id: str, content_type: str = None):
        try:
            file_path = self._generate_unique_filename(filename, user_id)
            file_options = {"content-type": content_type or "application/octet-stream"}

            # Cria arquivo temporário
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(file_content)
                tmp_path = tmp.name

            # Faz o upload
            self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=tmp_path,
                file_options=file_options
            )

            # Remove o arquivo temporário
            os.remove(tmp_path)

            public_url = self.client.storage.from_(self.bucket_name).get_public_url(file_path)
            return file_path, public_url

        except Exception as e:
            raise Exception(f"Erro ao fazer upload do arquivo: {e}")

    # ------------------------
    # Listagem de arquivos
    # ------------------------
    def list_files(self, user_id: str) -> List[dict]:
        """Lista todos os arquivos do usuário dentro do bucket"""
        try:
            return self.client.storage.from_(self.bucket_name).list(path=user_id)
        except Exception as e:
            raise Exception(f"Erro ao listar arquivos: {str(e)}")

    # ------------------------
    # Obter URL pública
    # ------------------------
    def get_public_url(self, file_path: str) -> str:
        """Obtém a URL pública de um arquivo"""
        try:
            return self.client.storage.from_(self.bucket_name).get_public_url(file_path)
        except Exception as e:
            raise Exception(f"Erro ao obter URL pública: {str(e)}")

    # ------------------------
    # Download de arquivo
    # ------------------------
    def download_file(self, file_path: str) -> bytes:
        """Faz download de um arquivo do storage"""
        try:
            response = self.client.storage.from_(self.bucket_name).download(file_path)
            return response
        except Exception as e:
            raise Exception(f"Erro ao fazer download do arquivo: {str(e)}")

    # ------------------------
    # Excluir arquivo
    # ------------------------
    async def delete_file(self, file_path: str) -> bool:
        """Remove um arquivo do storage"""
        try:
            self.client.storage.from_(self.bucket_name).remove([file_path])
            return True
        except Exception as e:
            raise Exception(f"Erro ao remover arquivo: {str(e)}")
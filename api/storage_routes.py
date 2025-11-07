from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from dependency_injector.wiring import inject, Provide
from datetime import datetime

from core.kernel.container import Container
from infrastructure.services.storage_service import StorageService
from api.dependencies import get_current_user
from domain.schema import FileUploadResponse, FileDeleteRequest

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.post("/upload", response_model=FileUploadResponse)
@inject
async def upload_file(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user),
    storage_service: StorageService = Depends(Provide[Container.storage_service])
):
    """
    Faz upload de um arquivo para o Supabase Storage.
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")

        content = await file.read()

        file_path, public_url = await storage_service.upload_file(
            file_content=content,
            filename=file.filename,
            user_id=user_id,
            content_type=file.content_type
        )

        return FileUploadResponse(
            file_path=file_path,
            public_url=public_url,
            filename=file.filename,
            uploaded_at=datetime.now().isoformat(),
            user_id=user_id
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao fazer upload: {str(e)}")


@router.get("/list")
@inject
async def list_files(
    user_id: str = Depends(get_current_user),
    storage_service: StorageService = Depends(Provide[Container.storage_service])
):
    """Lista os arquivos do usuário autenticado"""
    try:
        files = storage_service.list_files(user_id)
        return {"user_id": user_id, "files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar arquivos: {str(e)}")


@router.delete("/delete")
@inject
async def delete_file(
    request: FileDeleteRequest,
    user_id: str = Depends(get_current_user),
    storage_service: StorageService = Depends(Provide[Container.storage_service])
):
    """Remove um arquivo do Supabase Storage"""
    try:
        if not request.file_path.startswith(user_id):
            raise HTTPException(status_code=403, detail="Permissão negada")

        await storage_service.delete_file(request.file_path)
        return {"message": "Arquivo removido com sucesso", "file_path": request.file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao remover arquivo: {str(e)}")
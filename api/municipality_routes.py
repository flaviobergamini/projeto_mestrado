from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from dependency_injector.wiring import inject, Provide

from api.dependencies import get_current_user, require_roles
from core.kernel.container import Container
from infrastructure.repositories.municipality_repository import MunicipalityRepository

router = APIRouter(prefix="/municipalities", tags=["Municipalities"])


class MunicipalityBody(BaseModel):
    name: str


@router.get("")
@inject
async def list_municipalities(
    current_user: dict = Depends(get_current_user),
    repo: MunicipalityRepository = Depends(Provide[Container.municipality_repository]),
):
    return await repo.list_all()


@router.post("", status_code=201)
@inject
async def create_municipality(
    body: MunicipalityBody,
    current_user: dict = Depends(require_roles("admin")),
    repo: MunicipalityRepository = Depends(Provide[Container.municipality_repository]),
):
    return await repo.create(body.name)


@router.put("/{municipality_id}")
@inject
async def update_municipality(
    municipality_id: str,
    body: MunicipalityBody,
    current_user: dict = Depends(require_roles("admin")),
    repo: MunicipalityRepository = Depends(Provide[Container.municipality_repository]),
):
    result = await repo.update(municipality_id, body.name)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Município não encontrado.")
    return result


@router.delete("/{municipality_id}", status_code=204)
@inject
async def delete_municipality(
    municipality_id: str,
    current_user: dict = Depends(require_roles("admin")),
    repo: MunicipalityRepository = Depends(Provide[Container.municipality_repository]),
):
    deleted = await repo.delete(municipality_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Município não encontrado.")

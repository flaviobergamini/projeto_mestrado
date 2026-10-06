"""Perfil funcional do aluno. Camada HTTP apenas: a regra fica nos use cases."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Optional
from dependency_injector.wiring import inject, Provide

from api.dependencies import require_roles
from core.kernel.container import Container
from core.kernel.result import Result
from core.use_case.functional_profile import functional_profile_use_cases as uc

router = APIRouter(prefix="/functional-profiles", tags=["Functional Profile"])

READERS = ("admin", "coordenacao", "professor", "viewer")
WRITERS = ("admin", "coordenacao", "professor")


class GenerateBody(BaseModel):
    student_id: str
    sources: Optional[list[str]] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


class ProfileBody(BaseModel):
    student_id: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    content: Optional[dict[str, Any]] = None


def _unwrap(result: Result):
    if result.is_ok:
        return result.value
    if result.is_not_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result.not_found_error)
    if result.is_bad_request:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.bad_request_error)
    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result.error)


@router.get("/domains")
@inject
async def list_domains(
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListFunctionalDomainsUseCase = Depends(Provide[Container.list_functional_domains_use_case]),
):
    return _unwrap(await use_case.execute())


@router.post("/generate", status_code=status.HTTP_201_CREATED)
@inject
async def generate_profile(
    body: GenerateBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.GenerateFunctionalProfileUseCase = Depends(Provide[Container.generate_functional_profile_use_case]),
):
    return _unwrap(await use_case.execute(
        body.student_id, current_user, sources=body.sources, period_start=body.period_start,
        period_end=body.period_end, notes=body.notes,
    ))


@router.post("", status_code=status.HTTP_201_CREATED)
@inject
async def create_profile(
    body: ProfileBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.CreateManualProfileUseCase = Depends(Provide[Container.create_manual_profile_use_case]),
):
    return _unwrap(await use_case.execute(
        body.student_id, body.content, current_user, body.title, body.period_start, body.period_end,
    ))


@router.get("/student/{student_id}")
@inject
async def list_profiles(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.ListStudentProfilesUseCase = Depends(Provide[Container.list_student_profiles_use_case]),
):
    return _unwrap(await use_case.execute(student_id))


@router.get("/student/{student_id}/evolution")
@inject
async def evolution(
    student_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.GetProfileEvolutionUseCase = Depends(Provide[Container.get_profile_evolution_use_case]),
):
    return _unwrap(await use_case.execute(student_id))


@router.get("/{profile_id}")
@inject
async def get_profile(
    profile_id: str,
    current_user: dict = Depends(require_roles(*READERS)),
    use_case: uc.GetProfileUseCase = Depends(Provide[Container.get_profile_use_case]),
):
    return _unwrap(await use_case.execute(profile_id))


@router.put("/{profile_id}")
@inject
async def update_profile(
    profile_id: str,
    body: ProfileBody,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.UpdateProfileUseCase = Depends(Provide[Container.update_profile_use_case]),
):
    return _unwrap(await use_case.execute(
        profile_id, body.content, current_user, body.title, body.period_start, body.period_end,
        body.model_fields_set,
    ))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_profile(
    profile_id: str,
    current_user: dict = Depends(require_roles(*WRITERS)),
    use_case: uc.DeleteProfileUseCase = Depends(Provide[Container.delete_profile_use_case]),
):
    _unwrap(await use_case.execute(profile_id))

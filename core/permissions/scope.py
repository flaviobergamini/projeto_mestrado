"""
Filtros de escopo por role.

O escopo define quais registros cada usuário pode ver/editar,
baseado nos campos de vinculação do user_profiles (municipality_id,
school_id, teacher_id).

Uso nos use cases:
    scope = build_scope(user)
    # scope é um dict passado para os repositórios filtrarem as queries
"""

from core.permissions.roles import (
    ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, PESQUISADOR,
)


def build_scope(user: dict) -> dict:
    """
    Retorna o filtro de escopo para o usuário.

    Campos possíveis no retorno:
      - municipality_id : restringe ao município
      - school_id       : restringe à escola
      - teacher_id      : restringe ao professor (apenas seus alunos)
      - unrestricted    : True quando não há filtro (admin/pesquisador)
    """
    role = user.get("role")

    if role in (ADMIN, PESQUISADOR):
        return {"unrestricted": True}

    if role == SECRETARIA:
        return {"municipality_id": user.get("municipality_id")}

    if role == COORDENACAO:
        return {"school_id": user.get("school_id")}

    if role == PROFESSOR:
        return {
            "school_id": user.get("school_id"),
            "teacher_id": user.get("teacher_id"),
        }

    return {}


def scope_allows_school(scope: dict, school_municipality_id: str, school_id: str) -> bool:
    """Verifica se o escopo dá acesso a uma escola específica."""
    if scope.get("unrestricted"):
        return True
    if "municipality_id" in scope:
        return scope["municipality_id"] == school_municipality_id
    if "school_id" in scope:
        return scope["school_id"] == school_id
    return False


def scope_allows_student(scope: dict, student_school_id: str, student_teacher_ids: list) -> bool:
    """Verifica se o escopo dá acesso a um aluno específico."""
    if scope.get("unrestricted"):
        return True
    if "teacher_id" in scope:
        return scope["teacher_id"] in student_teacher_ids
    if "school_id" in scope:
        return scope["school_id"] == student_school_id
    return False

"""Testa as regras de RBAC em core/permissions/roles.py.

Estas regras são a base de segurança de todo o sistema multi-tenant — um erro
aqui (ex.: professor entrar em CAN_EDIT_TEACHER por engano) vaza dados entre
escolas/municípios diferentes silenciosamente. Cobrimos o caso positivo E o
caso negativo de cada permissão sensível.
"""

from core.permissions import roles


def test_only_admin_can_create_user():
    assert roles.can(roles.ADMIN, roles.CAN_CREATE_USER)
    for role in roles.ALL_ROLES - {roles.ADMIN}:
        assert not roles.can(role, roles.CAN_CREATE_USER), f"{role} não deveria criar usuários"


def test_only_admin_can_edit_teacher():
    assert roles.can(roles.ADMIN, roles.CAN_EDIT_TEACHER)
    for role in roles.ALL_ROLES - {roles.ADMIN}:
        assert not roles.can(role, roles.CAN_EDIT_TEACHER), f"{role} não deveria editar professores"


def test_professor_can_edit_student_but_not_school():
    assert roles.can(roles.PROFESSOR, roles.CAN_EDIT_STUDENT)
    assert not roles.can(roles.PROFESSOR, roles.CAN_EDIT_SCHOOL)


def test_secretaria_can_pre_register_but_not_edit_school():
    assert roles.can(roles.SECRETARIA, roles.CAN_PRE_REGISTER)
    assert not roles.can(roles.SECRETARIA, roles.CAN_EDIT_SCHOOL)


def test_viewer_is_read_only():
    assert roles.is_read_only(roles.VIEWER)
    for role in roles.ALL_ROLES - {roles.VIEWER}:
        assert not roles.is_read_only(role), f"{role} não deveria ser read-only"


def test_parent_and_therapist_are_scoped_roles():
    assert roles.PARENT in roles.SCOPED_ROLES
    assert roles.THERAPIST in roles.SCOPED_ROLES
    assert roles.ADMIN not in roles.SCOPED_ROLES


def test_only_parent_and_admin_can_write_family_diary():
    assert roles.can(roles.PARENT, roles.CAN_WRITE_FAMILY_DIARY)
    assert roles.can(roles.ADMIN, roles.CAN_WRITE_FAMILY_DIARY)
    assert not roles.can(roles.THERAPIST, roles.CAN_WRITE_FAMILY_DIARY)
    assert not roles.can(roles.PROFESSOR, roles.CAN_WRITE_FAMILY_DIARY)


def test_only_therapist_and_admin_can_write_therapy_diary():
    assert roles.can(roles.THERAPIST, roles.CAN_WRITE_THERAPY_DIARY)
    assert roles.can(roles.ADMIN, roles.CAN_WRITE_THERAPY_DIARY)
    assert not roles.can(roles.PARENT, roles.CAN_WRITE_THERAPY_DIARY)


def test_write_roles_and_read_only_roles_are_disjoint():
    assert roles.WRITE_ROLES.isdisjoint(roles.READ_ONLY_ROLES)


def test_all_write_permission_sets_are_subsets_of_all_roles():
    permission_sets = [
        roles.CAN_CREATE_USER, roles.CAN_PRE_REGISTER, roles.CAN_REGISTER_SCHOOL,
        roles.CAN_EDIT_SCHOOL, roles.CAN_VIEW_SCHOOL, roles.CAN_EDIT_STUDENT,
        roles.CAN_VIEW_STUDENT, roles.CAN_EDIT_TEACHER, roles.CAN_VIEW_TEACHER,
        roles.CAN_FILL_CASE_STUDY, roles.CAN_VIEW_CASE_STUDY, roles.CAN_USE_CHAT,
        roles.CAN_WRITE_FAMILY_DIARY, roles.CAN_WRITE_THERAPY_DIARY,
    ]
    for permission_set in permission_sets:
        assert permission_set <= roles.ALL_ROLES

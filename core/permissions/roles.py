"""
Roles e regras de acesso do sistema.

Hierarquia:
  admin        → acesso global, único que cadastra usuários
  secretaria   → pré-cadastro (escola, professor, aluno) por município — sem update
  coordenacao  → cadastra/edita escola; preenche estudo de caso; vê alunos da escola
  professor    → vê/edita apenas seus próprios alunos; preenche estudo de caso
  viewer       → leitura global, sem escrita
"""

# ------------------------------------------------------------------ #
# Constantes de role                                                  #
# ------------------------------------------------------------------ #
ADMIN = "admin"
SECRETARIA = "secretaria"
COORDENACAO = "coordenacao"
PROFESSOR = "professor"
VIEWER = "viewer"
PARENT = "parent"          # Responsável/familiar — acessa apenas seus filhos
THERAPIST = "therapist"    # Terapeuta — acessa apenas seus pacientes

ALL_ROLES = {ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, VIEWER, PARENT, THERAPIST}

# Roles que podem escrever dados
WRITE_ROLES = {ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, PARENT, THERAPIST}

# Roles somente leitura
READ_ONLY_ROLES = {VIEWER}

# Roles com acesso limitado a seus próprios alunos/pacientes
SCOPED_ROLES = {PARENT, THERAPIST}

# ------------------------------------------------------------------ #
# Permissões por recurso                                              #
# ------------------------------------------------------------------ #

# Quem pode cadastrar usuários
CAN_CREATE_USER = {ADMIN}

# Quem pode fazer pré-cadastro (escola, professor, aluno) — CREATE only, sem UPDATE
CAN_PRE_REGISTER = {ADMIN, SECRETARIA}

# Quem pode efetivar o cadastro da escola (a partir do pré-cadastro)
CAN_REGISTER_SCHOOL = {ADMIN, COORDENACAO}

# Quem pode editar escola
CAN_EDIT_SCHOOL = {ADMIN, COORDENACAO}

# Quem pode ver escolas
CAN_VIEW_SCHOOL = {ADMIN, SECRETARIA, COORDENACAO, VIEWER}

# Quem pode editar aluno
CAN_EDIT_STUDENT = {ADMIN, PROFESSOR}

# Quem pode ver alunos
CAN_VIEW_STUDENT = {ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, VIEWER}

# Quem pode editar professor/docente
CAN_EDIT_TEACHER = {ADMIN}

# Quem pode ver professores
CAN_VIEW_TEACHER = {ADMIN, SECRETARIA, COORDENACAO, VIEWER}

# Quem pode preencher estudo de caso / PDI
CAN_FILL_CASE_STUDY = {ADMIN, COORDENACAO, PROFESSOR}

# Quem pode ver estudos de caso
CAN_VIEW_CASE_STUDY = {ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, VIEWER}

# Quem pode usar o chat/RAG
CAN_USE_CHAT = {ADMIN, SECRETARIA, COORDENACAO, PROFESSOR, VIEWER}

# Quem pode registrar diário familiar
CAN_WRITE_FAMILY_DIARY = {ADMIN, PARENT}

# Quem pode registrar diário de terapia
CAN_WRITE_THERAPY_DIARY = {ADMIN, THERAPIST}

# Quem pode gerar Resumo Diário (chat com IA + salvar)
CAN_GENERATE_DIARY_SUMMARY = {ADMIN}

# Quem pode visualizar Resumos Diários já salvos
CAN_VIEW_DIARY_SUMMARY = {ADMIN, COORDENACAO, PROFESSOR, PARENT}


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def is_read_only(role: str) -> bool:
    return role in READ_ONLY_ROLES


def can(role: str, permission_set: set) -> bool:
    return role in permission_set

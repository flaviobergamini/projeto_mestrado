"""
Listas fixas (enums) usadas nas métricas de frequência/adesão do painel administrativo.

Mantidas como constantes de string (mesmo padrão de core/permissions/roles.py) e
reforçadas por CHECK constraints no banco (ver alembic/versions/0022_*), para que
as queries SQL de agregação possam confiar nos valores sem sanitização extra.
"""

# ------------------------------------------------------------------ #
# Nível de suporte do autismo (DSM-5)                                 #
# ------------------------------------------------------------------ #
SUPPORT_LEVEL_1 = "1"
SUPPORT_LEVEL_2 = "2"
SUPPORT_LEVEL_3 = "3"
AUTISM_SUPPORT_LEVELS = {SUPPORT_LEVEL_1, SUPPORT_LEVEL_2, SUPPORT_LEVEL_3}

# ------------------------------------------------------------------ #
# Papel do professor junto ao aluno com TEA                           #
# ------------------------------------------------------------------ #
TEACHER_ROLE_REGENTE = "regente"                # Professor(a) titular da turma
TEACHER_ROLE_APOIO = "apoio"                    # Professor(a) de apoio/mediador(a) — acompanha o aluno
TEACHER_ROLE_AEE = "aee"                        # Atendimento Educacional Especializado (sala de recursos)
TEACHER_ROLE_COORDENACAO_PEDAGOGICA = "coordenacao_pedagogica"
TEACHER_ROLE_OUTRO = "outro"
TEACHER_ROLES = {
    TEACHER_ROLE_REGENTE,
    TEACHER_ROLE_APOIO,
    TEACHER_ROLE_AEE,
    TEACHER_ROLE_COORDENACAO_PEDAGOGICA,
    TEACHER_ROLE_OUTRO,
}

# ------------------------------------------------------------------ #
# Gênero — usado apenas para a métrica de composição do corpo docente #
# ------------------------------------------------------------------ #
GENDER_FEMININO = "feminino"
GENDER_MASCULINO = "masculino"
GENDER_OUTRO = "outro"
GENDER_NAO_INFORMADO = "nao_informado"
GENDERS = {GENDER_FEMININO, GENDER_MASCULINO, GENDER_OUTRO, GENDER_NAO_INFORMADO}

# ------------------------------------------------------------------ #
# Faixa de renda familiar (em salários mínimos) — usada em vez do     #
# valor exato para reduzir a sensibilidade do dado coletado dos pais. #
# ------------------------------------------------------------------ #
INCOME_ATE_1_SM = "ate_1_sm"
INCOME_1_A_3_SM = "1_a_3_sm"
INCOME_3_A_5_SM = "3_a_5_sm"
INCOME_5_A_10_SM = "5_a_10_sm"
INCOME_ACIMA_10_SM = "acima_10_sm"
INCOME_NAO_INFORMADO = "nao_informado"
INCOME_BRACKETS = {
    INCOME_ATE_1_SM,
    INCOME_1_A_3_SM,
    INCOME_3_A_5_SM,
    INCOME_5_A_10_SM,
    INCOME_ACIMA_10_SM,
    INCOME_NAO_INFORMADO,
}

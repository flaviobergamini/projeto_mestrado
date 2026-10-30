"""Fontes de contexto do plano por habilidade. Os textos dos prompts ficam em core/constants/prompt_defaults.py."""

STAR_SCALE = (
    "0 = não iniciado; "
    "1 = dependência total (ajuda física total); "
    "2 = ajuda física parcial; "
    "3 = ajuda gestual ou verbal; "
    "4 = pista mínima/supervisão; "
    "5 = independente"
)

# Fontes FIXAS da geração das adaptações: pré-cadastro do aluno, perfil funcional e habilidades (relatório BNCC).
ROUND1_SOURCES = ["student", "functional_profile", "skill_report"]
# Limites MÁXIMOS da geração (ajustáveis pelo administrador na página de prompts). A IA usa menos quando o caso pede.
SKILL_PLAN_SETTINGS_KEY = "skill_plan_round1"
DEFAULT_SKILL_PLAN_LIMITS = {"max_adaptations": 3, "max_actions": 5}
LIMIT_RANGE = (1, 10)


from core.constants.prompt_defaults import SKILL_PLAN_ROUND1_PROMPT

ROUND1_SYSTEM = SKILL_PLAN_ROUND1_PROMPT

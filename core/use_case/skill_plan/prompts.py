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
# Fontes que o administrador pode ligar/desligar na página de prompts. As três primeiras do padrão são o histórico.
ROUND1_SOURCE_OPTIONS = ["student", "school", "case_study", "functional_profile", "skill_report", "diary_summary",
                         "student_documents"]
DIARY_SUMMARY_MONTHS = (1, 2, 3)  # janela dos resumos de diário: último mês, dois ou três meses
DEFAULT_SKILL_PLAN_LIMITS = {"max_adaptations": 3, "max_actions": 5}
DEFAULT_SKILL_PLAN_SETTINGS = {**DEFAULT_SKILL_PLAN_LIMITS, "sources": list(ROUND1_SOURCES), "diary_summary_months": 1}
LIMIT_RANGE = (1, 10)


def resolve_round1_settings(stored: dict | None) -> dict:
    """Configuração salva + padrões (configurações antigas só têm os limites). Fontes inválidas são descartadas."""
    merged = {**DEFAULT_SKILL_PLAN_SETTINGS, **(stored or {})}
    sources = [s for s in (merged.get("sources") or []) if s in ROUND1_SOURCE_OPTIONS] or list(ROUND1_SOURCES)
    months = merged.get("diary_summary_months")
    return {**merged, "sources": sources, "diary_summary_months": months if months in DIARY_SUMMARY_MONTHS else 1}


from core.constants.prompt_defaults import SKILL_PLAN_ROUND1_PROMPT

ROUND1_SYSTEM = SKILL_PLAN_ROUND1_PROMPT

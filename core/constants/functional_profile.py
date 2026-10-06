"""Perfil funcional do aluno: domínios avaliados e escala de apoio (1 a 5)."""

DOMAINS: list[tuple[str, str]] = [
    ("communication", "Comunicação e linguagem"),
    ("social", "Interação social"),
    ("behavior", "Comportamento e regulação emocional"),
    ("autonomy", "Autonomia e autocuidado"),
    ("learning", "Cognição e aprendizagem acadêmica"),
    ("sensory", "Perfil sensorial"),
    ("motor", "Motricidade (grossa e fina)"),
]
DOMAIN_LABELS: dict[str, str] = dict(DOMAINS)

# Nível = grau de independência/consolidação observado. None = sem evidência suficiente.
LEVEL_SCALE = (
    "1 = ainda não demonstra / precisa de apoio muito substancial; "
    "2 = emergente, precisa de apoio substancial; "
    "3 = em desenvolvimento, apoio moderado; "
    "4 = consolidado, com apoio pontual; "
    "5 = consolidado e independente em diferentes contextos"
)

# Fontes que o perfil funcional pode usar quando gerado por IA (nunca ele mesmo; diários não são mais entrada da IA).
DEFAULT_SOURCES = [
    "student", "school", "teacher", "case_study", "pdi", "generated_pei",
    "kanban_progress", "diary_summary", "skill_report", "bncc_catalog",
]

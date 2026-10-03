"""Perguntas padrão do diário escolar. Cada aluno herda esta lista até que a
coordenação a personalize. As chaves são os nomes das colunas de diary_entries
(por isso métricas, RAG e histórico continuam funcionando sem mudança)."""

DEFAULT_DIARY_QUESTIONS: list[tuple[str, str]] = [
    ("had_lunch", "Lanchou?"),
    ("participated_in_play", "Participou da brincadeira/atividade coletiva?"),
    ("teacher_attention", "Deu atenção à fala da professora?"),
    ("activity_interest", "Demonstrou interesse para as atividades?"),
    ("completed_activities", "Realizou as atividades propostas?"),
    ("bathroom_use", "Fez uso do banheiro?"),
    ("followed_agreements", "Cumpriu os combinados?"),
]

BUILTIN_KEYS: set[str] = {k for k, _ in DEFAULT_DIARY_QUESTIONS}
DEFAULT_LABELS: dict[str, str] = dict(DEFAULT_DIARY_QUESTIONS)

MAX_QUESTIONS_PER_STUDENT = 30
MAX_LABEL_LENGTH = 300

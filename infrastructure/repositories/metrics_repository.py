"""Métricas agregadas de frequência/adesão para o painel administrativo.

Todas as consultas são feitas via SQL (agregação/GROUP BY no banco) em vez de
carregar linhas e agregar em Python — conforme pedido, para não pagar o custo de
trazer milhares de diary_entries pra memória a cada carregamento do painel.

Faixas etárias e de renda são calculadas a partir de birth_year/age (não de datas
completas), reduzindo a granularidade do dado sensível sem perder a métrica.
"""
from datetime import date, timedelta
from typing import Optional
from sqlalchemy import select, text
from infrastructure.database_context.database import Database
from infrastructure.models.diary_entry import DiaryEntry
from infrastructure.models.student import Student

# Painel de métricas carregava o histórico inteiro de diary_entries por
# padrão (sem date_from/date_to informados) — full scan a cada abertura da
# página, mesmo pros gráficos que só fazem sentido olhando um recorte recente.
# Sem filtro explícito do usuário, a própria query no banco já limita à última
# semana, em vez de escanear tudo e limitar depois em Python.
_DEFAULT_WINDOW_DAYS = 7


def _default_window(date_from: Optional[date], date_to: Optional[date]) -> tuple[date, date]:
    if date_from is None and date_to is None:
        today = date.today()
        return today - timedelta(days=_DEFAULT_WINDOW_DAYS), today
    return date_from, date_to

# Bucket de idade reutilizado nas queries de aluno (coluna students.age, string livre).
_STUDENT_AGE_BUCKET_SQL = """
    CASE
        WHEN s.age ~ '^[0-9]+$' AND s.age::int <= 6 THEN '0-6'
        WHEN s.age ~ '^[0-9]+$' AND s.age::int <= 9 THEN '7-9'
        WHEN s.age ~ '^[0-9]+$' AND s.age::int <= 12 THEN '10-12'
        WHEN s.age ~ '^[0-9]+$' AND s.age::int <= 15 THEN '13-15'
        WHEN s.age ~ '^[0-9]+$' AND s.age::int <= 18 THEN '16-18'
        WHEN s.age ~ '^[0-9]+$' THEN '19+'
        ELSE 'nao_informado'
    END
"""

# Bucket de idade a partir de birth_year (professores e responsáveis).
_BIRTH_YEAR_AGE_BUCKET_SQL = """
    CASE
        WHEN {col} IS NULL THEN 'nao_informado'
        WHEN (EXTRACT(YEAR FROM now()) - {col}) < 25 THEN 'ate_24'
        WHEN (EXTRACT(YEAR FROM now()) - {col}) < 35 THEN '25_a_34'
        WHEN (EXTRACT(YEAR FROM now()) - {col}) < 45 THEN '35_a_44'
        WHEN (EXTRACT(YEAR FROM now()) - {col}) < 55 THEN '45_a_54'
        ELSE '55_mais'
    END
"""


class MetricsRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    # ── Frequência de preenchimento × idade do aluno, segregado por escola/município ──

    async def diary_fill_by_student_age(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
        source: str = "school",
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        query = text(f"""
            SELECT
                m.name AS municipality_name,
                sc.name AS school_name,
                {_STUDENT_AGE_BUCKET_SQL} AS age_bucket,
                COUNT(DISTINCT s.id) AS student_count,
                COUNT(d.id) AS entry_count,
                ROUND(COUNT(d.id)::numeric / NULLIF(COUNT(DISTINCT s.id), 0), 2) AS avg_entries_per_student
            FROM students s
            LEFT JOIN schools sc ON sc.id = s.school_id
            LEFT JOIN municipalities m ON m.id = sc.municipality_id
            LEFT JOIN diary_entries d ON d.student_id = s.id
                AND d.deleted = false
                AND d.source = :source
                AND (CAST(:date_from AS date) IS NULL OR d.diary_date >= :date_from)
                AND (CAST(:date_to AS date) IS NULL OR d.diary_date <= :date_to)
            WHERE s.deleted = false
            GROUP BY m.name, sc.name, age_bucket
            ORDER BY m.name, sc.name, age_bucket
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"date_from": date_from, "date_to": date_to, "source": source})
            return [dict(row._mapping) for row in result.all()]

    # ── Frequência de preenchimento × nível de suporte do autismo ──────────────────

    async def diary_fill_by_support_level(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
        source: str = "school",
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        query = text("""
            SELECT
                COALESCE(s.autism_support_level, 'nao_informado') AS support_level,
                COUNT(DISTINCT s.id) AS student_count,
                COUNT(d.id) AS entry_count,
                ROUND(COUNT(d.id)::numeric / NULLIF(COUNT(DISTINCT s.id), 0), 2) AS avg_entries_per_student
            FROM students s
            LEFT JOIN diary_entries d ON d.student_id = s.id
                AND d.deleted = false
                AND d.source = :source
                AND (CAST(:date_from AS date) IS NULL OR d.diary_date >= :date_from)
                AND (CAST(:date_to AS date) IS NULL OR d.diary_date <= :date_to)
            WHERE s.deleted = false
            GROUP BY support_level
            ORDER BY support_level
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"date_from": date_from, "date_to": date_to, "source": source})
            return [dict(row._mapping) for row in result.all()]

    # ── Faltas por tipo (justificada/injustificada) ─────────────────────────────────

    async def absences_by_type(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
        school_id: Optional[str] = None,
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        query = text("""
            SELECT
                sc.name AS school_name,
                d.presence,
                COUNT(*) AS occurrence_count,
                COUNT(DISTINCT d.student_id) AS student_count
            FROM diary_entries d
            JOIN students s ON s.id = d.student_id AND s.deleted = false
            LEFT JOIN schools sc ON sc.id = s.school_id
            WHERE d.deleted = false
                AND d.source = 'school'
                AND d.presence IN ('Falta Justificada', 'Falta Injustificada')
                AND (CAST(:date_from AS date) IS NULL OR d.diary_date >= :date_from)
                AND (CAST(:date_to AS date) IS NULL OR d.diary_date <= :date_to)
                AND (CAST(:school_id AS varchar) IS NULL OR s.school_id = :school_id)
            GROUP BY sc.name, d.presence
            ORDER BY sc.name, d.presence
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"date_from": date_from, "date_to": date_to, "school_id": school_id})
            return [dict(row._mapping) for row in result.all()]

    # ── Índice de alunos por professor ──────────────────────────────────────────────

    async def students_per_teacher(self, school_id: Optional[str] = None) -> list[dict]:
        query = text("""
            SELECT
                sc.name AS school_name,
                COUNT(DISTINCT t.id) AS teacher_count,
                COUNT(DISTINCT tsl.student_id) AS student_count,
                ROUND(COUNT(DISTINCT tsl.student_id)::numeric / NULLIF(COUNT(DISTINCT t.id), 0), 2) AS students_per_teacher
            FROM teachers t
            LEFT JOIN teacher_student_links tsl ON tsl.teacher_id = t.id AND tsl.deleted = false
            LEFT JOIN schools sc ON sc.id = t.school_id
            WHERE t.deleted = false
                AND (CAST(:school_id AS varchar) IS NULL OR t.school_id = :school_id)
            GROUP BY sc.name
            ORDER BY sc.name
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"school_id": school_id})
            return [dict(row._mapping) for row in result.all()]

    # ── Composição do corpo docente (idade, gênero, especialidade) ─────────────────

    async def teacher_demographics(self, school_id: Optional[str] = None) -> list[dict]:
        query = text(f"""
            SELECT
                sc.name AS school_name,
                COALESCE(t.gender, 'nao_informado') AS gender,
                COALESCE(t.teacher_role, 'nao_informado') AS teacher_role,
                {_BIRTH_YEAR_AGE_BUCKET_SQL.format(col='t.birth_year')} AS age_bucket,
                COUNT(*) AS teacher_count
            FROM teachers t
            LEFT JOIN schools sc ON sc.id = t.school_id
            WHERE t.deleted = false
                AND (CAST(:school_id AS varchar) IS NULL OR t.school_id = :school_id)
            GROUP BY sc.name, gender, teacher_role, age_bucket
            ORDER BY sc.name, gender, teacher_role
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"school_id": school_id})
            return [dict(row._mapping) for row in result.all()]

    # ── Frequência de preenchimento × especialidade/gênero/idade do professor ──────
    # (via teacher_student_links, não via diary_entries.teacher_name — esse campo é
    # texto livre criptografado e pode conter vários nomes; o vínculo estruturado é
    # a única forma confiável de relacionar aluno → professor.)

    async def diary_fill_by_teacher_attributes(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        query = text(f"""
            SELECT
                COALESCE(t.teacher_role, 'nao_informado') AS teacher_role,
                COALESCE(t.gender, 'nao_informado') AS gender,
                {_BIRTH_YEAR_AGE_BUCKET_SQL.format(col='t.birth_year')} AS age_bucket,
                COUNT(DISTINCT tsl.student_id) AS student_count,
                COUNT(d.id) AS entry_count,
                ROUND(COUNT(d.id)::numeric / NULLIF(COUNT(DISTINCT tsl.student_id), 0), 2) AS avg_entries_per_student
            FROM teachers t
            JOIN teacher_student_links tsl ON tsl.teacher_id = t.id AND tsl.deleted = false
            LEFT JOIN diary_entries d ON d.student_id = tsl.student_id
                AND d.deleted = false
                AND d.source = 'school'
                AND (CAST(:date_from AS date) IS NULL OR d.diary_date >= :date_from)
                AND (CAST(:date_to AS date) IS NULL OR d.diary_date <= :date_to)
            WHERE t.deleted = false
            GROUP BY teacher_role, gender, age_bucket
            ORDER BY teacher_role, gender, age_bucket
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"date_from": date_from, "date_to": date_to})
            return [dict(row._mapping) for row in result.all()]

    # ── Frequência de preenchimento (diário familiar) × perfil do responsável ──────

    async def diary_fill_by_parent_profile(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        query = text(f"""
            SELECT
                COALESCE(up.income_bracket, 'nao_informado') AS income_bracket,
                CASE
                    WHEN up.single_parent IS TRUE THEN 'sim'
                    WHEN up.single_parent IS FALSE THEN 'nao'
                    ELSE 'nao_informado'
                END AS single_parent,
                {_BIRTH_YEAR_AGE_BUCKET_SQL.format(col='up.birth_year')} AS parent_age_bucket,
                COUNT(DISTINCT psl.student_id) AS student_count,
                COUNT(d.id) AS entry_count,
                ROUND(COUNT(d.id)::numeric / NULLIF(COUNT(DISTINCT psl.student_id), 0), 2) AS avg_entries_per_student
            FROM user_profiles up
            JOIN parent_student_links psl ON psl.parent_user_id = up.id AND psl.deleted = false
            LEFT JOIN diary_entries d ON d.student_id = psl.student_id
                AND d.deleted = false
                AND d.source = 'family'
                AND (CAST(:date_from AS date) IS NULL OR d.diary_date >= :date_from)
                AND (CAST(:date_to AS date) IS NULL OR d.diary_date <= :date_to)
            WHERE up.deleted = false AND up.role = 'parent'
            GROUP BY income_bracket, single_parent, parent_age_bucket
            ORDER BY income_bracket, single_parent, parent_age_bucket
        """)
        async with self.database.session() as session:
            result = await session.execute(query, {"date_from": date_from, "date_to": date_to})
            return [dict(row._mapping) for row in result.all()]

    # ── Correlação nível de suporte × comportamentos registrados no diário ─────────
    # (perguntas fechadas Sim/Não/Parcialmente do diário escolar — % de "Sim" por
    # pergunta, agrupado por nível de suporte, pra buscar correlação comportamental.)

    _BEHAVIOR_QUESTIONS = (
        "had_lunch", "participated_in_play", "teacher_attention", "activity_interest",
        "completed_activities", "bathroom_use", "followed_agreements",
    )

    async def behavior_by_support_level(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None,
    ) -> list[dict]:
        date_from, date_to = _default_window(date_from, date_to)
        # As respostas do diário (had_lunch, participated_in_play, etc.) são
        # EncryptedText — Fernet usa IV aleatório, então duas respostas 'Sim'
        # nunca têm o mesmo ciphertext. Um `WHERE d.had_lunch = 'Sim'` em SQL
        # bruto compara contra o valor cifrado e nunca bate com nada (sempre
        # 0%) — precisa carregar via ORM pra decriptar e agregar em Python.
        stmt = (
            select(DiaryEntry, Student.autism_support_level)
            .join(Student, Student.id == DiaryEntry.student_id)
            .where(
                Student.deleted == False,  # noqa: E712
                DiaryEntry.deleted == False,  # noqa: E712
                DiaryEntry.source == "school",
                DiaryEntry.presence == "Presente",
            )
        )
        if date_from is not None:
            stmt = stmt.where(DiaryEntry.diary_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(DiaryEntry.diary_date <= date_to)

        async with self.database.session() as session:
            rows = (await session.execute(stmt)).all()

        buckets: dict[str, dict] = {}
        for entry, support_level in rows:
            level = support_level or "nao_informado"
            bucket = buckets.setdefault(level, {
                "entry_count": 0,
                **{q: {"yes": 0, "answered": 0} for q in self._BEHAVIOR_QUESTIONS},
            })
            bucket["entry_count"] += 1
            for q in self._BEHAVIOR_QUESTIONS:
                answer = getattr(entry, q)
                if answer is not None:
                    bucket[q]["answered"] += 1
                    if answer == "Sim":
                        bucket[q]["yes"] += 1

        def _pct(counts: dict) -> Optional[float]:
            if not counts["answered"]:
                return None
            return round(100.0 * counts["yes"] / counts["answered"], 1)

        return [
            {
                "support_level": level,
                "entry_count": bucket["entry_count"],
                **{f"pct_{q}": _pct(bucket[q]) for q in self._BEHAVIOR_QUESTIONS},
            }
            for level, bucket in sorted(buckets.items())
        ]

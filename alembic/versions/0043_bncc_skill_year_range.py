"""habilidade BNCC cadastrada uma única vez, vinculada a um intervalo de anos

Revision ID: 0043_bncc_year_range
Revises: 0042_app_settings
Create Date: 2026-10-28

Até aqui o catálogo tinha UMA LINHA POR ANO para o mesmo código (ex.: EF15LP01 aparecia no 2º, 3º, 4º e 5º ano), e a
nota (estrelas), as adaptações e os cards do Kanban ficavam presos a cada linha: mexer em um ano não refletia nos outros.

Agora cada código existe uma única vez, com `grade_from` e `grade_to`. Nos códigos do Ensino Fundamental os dois
algarismos depois de "EF" dizem os anos: EF15 = do 1º ao 5º; EF35 = do 3º ao 5º; EF12 = do 1º ao 2º; EF05 = só o 5º.
Educação Infantil fica em 0..0. Códigos que fogem do padrão usam os anos em que já estavam cadastrados.

Para cada código repetido a migração:
  1. escolhe a linha do ano mais antigo como a definitiva;
  2. aponta para ela tudo o que dependia das outras linhas (notas, histórico, sugestões, resumos mensais, cards do
     Kanban, resultados salvos). Se o mesmo aluno tinha nota em mais de uma linha, fica a nota MAIS ALTA e os textos da
     linha mexida por último;
  3. apaga as linhas repetidas.
Antes de apagar, copia as linhas repetidas e as notas envolvidas para `bncc_skills_dedup_backup` e
`student_skill_scores_dedup_backup` (pode apagar essas tabelas depois de conferir).
"""
import re
from collections import defaultdict
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0043_bncc_year_range'
down_revision: Union[str, Sequence[str], None] = '0042_app_settings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

CODE_YEARS = re.compile(r"^EF(\d)(\d)")

# colunas de student_skill_scores que viajam juntas quando uma linha vence a outra
SCORE_TEXT_COLUMNS = (
    "observation", "summary", "adaptation", "justification", "actions", "correlated_codes",
    "ai_excluded", "in_plan", "plan_ai_at", "updated_by_user_id", "updated_by_username",
)


def year_range(code: str, orders: list[int], stage: str) -> tuple[int, int]:
    if stage == "infantil":
        return 0, 0
    m = CODE_YEARS.match(code)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a == 0:
            return b, b
        if 1 <= a <= b <= 5:
            return a, b
    return min(orders), max(orders)


def label(stage: str, y_from: int, y_to: int, current: str) -> str:
    if stage == "infantil":
        return current
    return f"{y_from}º ano" if y_from == y_to else f"{y_from}º ao {y_to}º ano"


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('bncc_skills', sa.Column('grade_from', sa.SmallInteger(), nullable=True))
    op.add_column('bncc_skills', sa.Column('grade_to', sa.SmallInteger(), nullable=True))

    rows = bind.execute(sa.text(
        "SELECT id, code, stage, grade, grade_order, created_at FROM bncc_skills WHERE deleted = false "
        "ORDER BY grade_order, created_at, id"
    )).fetchall()
    groups: dict[str, list] = defaultdict(list)
    for r in rows:
        groups[r.code].append(r)

    duplicates = [(code, rs) for code, rs in groups.items() if len(rs) > 1]
    if duplicates:
        dup_ids = [r.id for _, rs in duplicates for r in rs[1:]]
        bind.execute(sa.text("DROP TABLE IF EXISTS bncc_skills_dedup_backup"))
        bind.execute(sa.text("DROP TABLE IF EXISTS student_skill_scores_dedup_backup"))
        bind.execute(sa.text("CREATE TABLE bncc_skills_dedup_backup AS SELECT * FROM bncc_skills WHERE id = ANY(:ids)"),
                     {"ids": dup_ids})
        all_ids = [r.id for _, rs in duplicates for r in rs]
        bind.execute(sa.text("CREATE TABLE student_skill_scores_dedup_backup AS SELECT * FROM student_skill_scores "
                             "WHERE skill_id = ANY(:ids)"), {"ids": all_ids})

    for code, rs in groups.items():
        keep = rs[0]
        y_from, y_to = year_range(code, [r.grade_order for r in rs], keep.stage)
        bind.execute(sa.text(
            "UPDATE bncc_skills SET grade_from = :f, grade_to = :t, grade_order = :o, grade = :g WHERE id = :id"),
            {"f": y_from, "t": y_to, "o": y_from, "g": label(keep.stage, y_from, y_to, keep.grade), "id": keep.id})
        for dup in rs[1:]:
            _merge(bind, keep.id, dup.id)

    # linhas apagadas (deleted = true) e qualquer resto sem intervalo: usam o próprio ano
    bind.execute(sa.text("UPDATE bncc_skills SET grade_from = grade_order, grade_to = grade_order WHERE grade_from IS NULL"))
    op.alter_column('bncc_skills', 'grade_from', nullable=False, server_default='0')
    op.alter_column('bncc_skills', 'grade_to', nullable=False, server_default='0')
    op.create_index('uq_bncc_skills_code', 'bncc_skills', ['code'], unique=True, postgresql_where=sa.text('deleted = false'))
    op.create_index('ix_bncc_skills_year_range', 'bncc_skills', ['grade_from', 'grade_to'])


def _merge(bind, keep_id: str, dup_id: str) -> None:
    # notas por aluno: mesmo aluno nas duas linhas -> maior nota, textos da linha mexida por último
    clash = bind.execute(sa.text(
        "SELECT d.student_id, d.score AS dscore, d.updated_at AS dupd, k.score AS kscore, k.updated_at AS kupd "
        "FROM student_skill_scores d JOIN student_skill_scores k ON k.student_id = d.student_id AND k.skill_id = :keep "
        "WHERE d.skill_id = :dup"), {"keep": keep_id, "dup": dup_id}).fetchall()
    for c in clash:
        best = max(c.dscore or 0, c.kscore or 0)
        if (c.dupd or c.kupd) and c.dupd and (not c.kupd or c.dupd > c.kupd):
            sets = ", ".join(f"{col} = d.{col}" for col in SCORE_TEXT_COLUMNS)
            bind.execute(sa.text(
                f"UPDATE student_skill_scores k SET {sets} FROM student_skill_scores d "
                "WHERE k.student_id = :s AND k.skill_id = :keep AND d.student_id = :s AND d.skill_id = :dup"),
                {"s": c.student_id, "keep": keep_id, "dup": dup_id})
        bind.execute(sa.text("UPDATE student_skill_scores SET score = :b WHERE student_id = :s AND skill_id = :keep"),
                     {"b": best, "s": c.student_id, "keep": keep_id})
        bind.execute(sa.text("DELETE FROM student_skill_scores WHERE student_id = :s AND skill_id = :dup"),
                     {"s": c.student_id, "dup": dup_id})
    bind.execute(sa.text("UPDATE student_skill_scores SET skill_id = :keep WHERE skill_id = :dup"), {"keep": keep_id, "dup": dup_id})

    # resumo mensal tem UNIQUE (aluno, habilidade, mês): onde já existe na definitiva, descarta o da repetida
    bind.execute(sa.text(
        "DELETE FROM skill_monthly_snapshots d USING skill_monthly_snapshots k "
        "WHERE d.skill_id = :dup AND k.skill_id = :keep AND k.student_id = d.student_id AND k.month = d.month"),
        {"keep": keep_id, "dup": dup_id})
    for table in ("student_skill_events", "skill_suggestions", "skill_monthly_snapshots", "pei_kanban_cards", "saved_skill_results"):
        bind.execute(sa.text(f"UPDATE {table} SET skill_id = :keep WHERE skill_id = :dup"), {"keep": keep_id, "dup": dup_id})
    bind.execute(sa.text("DELETE FROM bncc_skills WHERE id = :dup"), {"dup": dup_id})


def downgrade() -> None:
    # os dados continuam sem repetição (as cópias de segurança ficam em *_dedup_backup); só remove as colunas novas
    op.drop_index('ix_bncc_skills_year_range', table_name='bncc_skills')
    op.drop_index('uq_bncc_skills_code', table_name='bncc_skills')
    op.drop_column('bncc_skills', 'grade_to')
    op.drop_column('bncc_skills', 'grade_from')

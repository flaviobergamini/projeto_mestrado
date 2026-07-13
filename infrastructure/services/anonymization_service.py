"""Anonymization service — strips PII before sending data to Gemini.

Pipeline:
  1. On create/update: repositories compute anonymized JSON and store it in
     `anonymized_data` column (TEXT, JSON-encoded) of each table.
  2. At prompt-build time: AnonymizationService reads the pre-computed columns —
     never touches PII fields.
  3. After Gemini responds: deanonymize() replaces UUIDs with real names.

What is stripped per entity:
  Student   → name, birth_date, guardians  | kept: id, school_id, age, grade, class_name, diagnosis
  School    → name, cnpj, address_city     | kept: id, institution_type
  Teacher   → name, email, phone           | kept: id, school_id, specialization
  DiaryEntry→ teacher_name                 | kept: student_id, diary_date, presence, all activity fields
  CaseStudy → studentName, schoolName, mainTeacher, supportTeacher, submitted_by
"""

import json
import logging
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from infrastructure.database_context.database import Database
from infrastructure.models.student import Student
from infrastructure.models.school import School
from infrastructure.models.teacher import Teacher
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.models.diary_entry import DiaryEntry

logger = logging.getLogger(__name__)

# ── Pure anonymization functions (called at write time in repositories) ────────

def anon_student(student: dict) -> dict:
    """Keep only non-PII student fields. Called in StudentRepository on create/update."""
    return {
        "student_id": student.get("id") or "",
        "school_id": student.get("school_id") or "",
        "age": student.get("age") or "",
        "grade": student.get("grade") or "",
        "class_name": student.get("class_name") or "",
        "diagnosis": student.get("diagnosis") or "",
    }


def anon_school(school: dict | None) -> dict:
    """Keep only non-PII school fields."""
    if not school:
        return {}
    return {
        "school_id": school.get("id") or "",
        "institution_type": school.get("institution_type") or "",
    }


def anon_teacher(teacher: dict) -> dict:
    """Keep only non-PII teacher fields."""
    return {
        "teacher_id": teacher.get("id") or "",
        "school_id": teacher.get("school_id") or "",
        "specialization": teacher.get("specialization") or "",
    }


def anon_diary_entry(entry: dict, school_id: str = "") -> dict:
    """Strip teacher_name; keep all activity/observation fields. Called in DiaryRepository."""
    presenca = entry.get("presence") or "Não informado"
    is_present = presenca.lower() == "presente"

    data: dict = {
        "student_id": entry.get("student_id") or "",
        "school_id": school_id,
        "diary_date": str(entry.get("diary_date") or ""),
        "presence": presenca,
    }

    if is_present:
        data["activities"] = {
            "teacher_attention": entry.get("teacher_attention") or "",
            "followed_agreements": entry.get("followed_agreements") or "",
            "activity_interest": entry.get("activity_interest") or "",
            "had_lunch": entry.get("had_lunch") or "",
            "participated_in_play": entry.get("participated_in_play") or "",
            "completed_activities": entry.get("completed_activities") or "",
            "bathroom_use": entry.get("bathroom_use") or "",
        }
        if entry.get("open_observation"):
            data["open_observation"] = entry["open_observation"]
    else:
        if entry.get("absence_reason"):
            data["absence_reason"] = entry["absence_reason"]

    return data


def anon_case_study(case: dict) -> dict:
    """Strip PII answer fields from a case study. Kept: student_id, behavioral/pedagogical answers."""
    answers = case.get("answers") or {}
    PII_KEYS = {"studentName", "schoolName", "mainTeacher", "supportTeacher"}
    clean_answers = {k: v for k, v in answers.items() if k not in PII_KEYS}
    return {
        "student_id": case.get("student_id") or "",
        "submitted_at": (case.get("submitted_at") or "")[:10],
        "answers": clean_answers,
    }


# ── De-anonymization ──────────────────────────────────────────────────────────

def build_deanon_map(
    student: dict,
    school: dict | None,
    teachers: list[dict],
) -> dict[str, str]:
    """Build UUID → real name map for replacing UUIDs in Gemini output."""
    name_map: dict[str, str] = {}

    if (sid := student.get("id")) and (sname := student.get("name")):
        name_map[sid] = sname
    if school:
        if (scid := school.get("id")) and (scname := school.get("name")):
            name_map[scid] = scname
    for t in teachers:
        if (tid := t.get("id")) and (tname := t.get("name")):
            name_map[tid] = tname

    return name_map


def deanonymize(text: str, name_map: dict[str, str]) -> str:
    """Replace all UUIDs in Gemini output with their real names."""
    for uuid, real_name in name_map.items():
        text = text.replace(uuid, real_name)
    return text


# ── Service class ─────────────────────────────────────────────────────────────

class AnonymizationService:
    """Reads pre-computed anonymized_data columns and assembles the Gemini context."""

    def __init__(self, database: Database):
        self._db = database

    async def build_context(
        self,
        student_id: str,
        diary_limit: int = 10,
    ) -> tuple[str, dict[str, str]]:
        """Return (anonymized_context_str, deanon_map).

        Reads from `anonymized_data` columns — never touches PII fields.
        Falls back to computing on-the-fly for rows that predate the migration
        (anonymized_data IS NULL).
        """
        async with self._db.session() as session:
            # ── Student ──────────────────────────────────────────────────────
            student_row = await session.get(Student, student_id)
            if not student_row:
                return ("Aluno não encontrado.", {})

            student_dict = {
                "id": student_row.id,
                "school_id": student_row.school_id,
                "name": student_row.name,
                "age": student_row.age,
                "grade": student_row.grade,
                "class_name": student_row.class_name,
                "diagnosis": student_row.diagnosis,
            }

            # Read pre-computed or fall back
            if student_row.anonymized_data:
                student_anon = json.loads(student_row.anonymized_data)
            else:
                student_anon = anon_student(student_dict)

            # ── School ───────────────────────────────────────────────────────
            school_dict = None
            school_anon: dict = {}
            if student_row.school_id:
                school_row = await session.get(School, student_row.school_id)
                if school_row:
                    school_dict = {"id": school_row.id, "name": school_row.name,
                                   "institution_type": school_row.institution_type}
                    school_anon = anon_school(school_dict)

            # ── Linked teachers ──────────────────────────────────────────────
            links_result = await session.execute(
                select(TeacherStudentLink)
                .options(selectinload(TeacherStudentLink.teacher))
                .where(TeacherStudentLink.student_id == student_id)
            )
            teacher_dicts: list[dict] = []
            teachers_anon: list[dict] = []
            for link in links_result.scalars().all():
                t = link.teacher
                if t:
                    td = {"id": t.id, "name": t.name, "school_id": t.school_id,
                          "specialization": t.specialization}
                    teacher_dicts.append(td)
                    teachers_anon.append(anon_teacher(td))

            # ── Recent diary entries ─────────────────────────────────────────
            diary_result = await session.execute(
                select(DiaryEntry)
                .where(DiaryEntry.student_id == student_id)
                .order_by(DiaryEntry.diary_date.desc())
                .limit(diary_limit)
            )
            diary_rows = diary_result.scalars().all()

            school_id = student_row.school_id or ""
            diary_anon_list: list[dict] = []
            for e in diary_rows:
                if e.anonymized_data:
                    # Pre-computed — inject school_id since it's not stored in diary's column
                    d = json.loads(e.anonymized_data)
                    d["school_id"] = school_id
                    diary_anon_list.append(d)
                else:
                    # Fallback for rows that predate the migration
                    entry_dict = {
                        "student_id": e.student_id,
                        "diary_date": str(e.diary_date) if e.diary_date else "",
                        "presence": e.presence,
                        "teacher_attention": e.teacher_attention,
                        "followed_agreements": e.followed_agreements,
                        "activity_interest": e.activity_interest,
                        "had_lunch": e.had_lunch,
                        "participated_in_play": e.participated_in_play,
                        "completed_activities": e.completed_activities,
                        "bathroom_use": e.bathroom_use,
                        "open_observation": e.open_observation,
                        "absence_reason": e.absence_reason,
                    }
                    diary_anon_list.append(anon_diary_entry(entry_dict, school_id=school_id))

        # ── De-anonymization map ──────────────────────────────────────────────
        deanon_map = build_deanon_map(student_dict, school_dict, teacher_dicts)

        # ── Assemble context string ───────────────────────────────────────────
        sections: list[str] = []

        sections.append("=== DADOS DO ALUNO (ANONIMIZADOS) ===")
        sections.append(json.dumps(student_anon, ensure_ascii=False, indent=2))

        if school_anon:
            sections.append("=== ESCOLA (ANONIMIZADA) ===")
            sections.append(json.dumps(school_anon, ensure_ascii=False, indent=2))

        if teachers_anon:
            sections.append("=== DOCENTES VINCULADOS (ANONIMIZADOS) ===")
            sections.append(json.dumps(teachers_anon, ensure_ascii=False, indent=2))

        if diary_anon_list:
            sections.append(f"=== DIÁRIO RECENTE (últimas {len(diary_anon_list)} entradas, ANONIMIZADO) ===")
            sections.append(json.dumps(diary_anon_list, ensure_ascii=False, indent=2))

        context_str = "\n\n".join(sections)
        return context_str, deanon_map

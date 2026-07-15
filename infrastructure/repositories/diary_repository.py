import uuid
import json
from datetime import date
from typing import Optional
from sqlalchemy import select, func, delete
from infrastructure.database_context.database import Database
from infrastructure.models.diary_entry import DiaryEntry
from infrastructure.models.student import Student
from infrastructure.models.teacher_student_link import TeacherStudentLink
from infrastructure.models.teacher import Teacher
from infrastructure.models.object_storage_file import ObjectStorageFile
from infrastructure.services.anonymization_service import anon_diary_entry


def _build_diary_anonymized(entry_data: dict) -> str:
    return json.dumps(anon_diary_entry(entry_data), ensure_ascii=False)


def _to_dict(e: DiaryEntry) -> dict:
    return {
        "id": e.id,
        "student_id": e.student_id,
        "diary_date": e.diary_date.isoformat() if e.diary_date else None,
        "teacher_attention": e.teacher_attention,
        "followed_agreements": e.followed_agreements,
        "activity_interest": e.activity_interest,
        "had_lunch": e.had_lunch,
        "participated_in_play": e.participated_in_play,
        "completed_activities": e.completed_activities,
        "bathroom_use": e.bathroom_use,
        "open_observation": e.open_observation,
        "absence_reason": e.absence_reason,
        "teacher_name": e.teacher_name,
        "presence": e.presence,
        "status": e.status,
        "source": e.source,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "updated_at": e.updated_at.isoformat() if e.updated_at else None,
    }


class DiaryRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    async def list_students_with_diary(self) -> list[dict]:
        """Returns one summary entry per student that has at least one diary entry."""
        async with self.database.session() as session:
            # Aggregate per student
            stmt = (
                select(
                    DiaryEntry.student_id,
                    Student.name.label("student_name"),
                    func.max(DiaryEntry.diary_date).label("last_entry"),
                    func.count(DiaryEntry.id).label("total_entries"),
                )
                .outerjoin(Student, DiaryEntry.student_id == Student.id)
                .where(DiaryEntry.deleted == False)
                .group_by(DiaryEntry.student_id, Student.name)
                .order_by(Student.name)
            )
            
            result = await session.execute(stmt)

            rows = result.all()

            return [
                {
                    "student_id": row.student_id,
                    "student_name": row.student_name or row.student_id,
                    "last_entry": row.last_entry.isoformat() if row.last_entry else None,
                    "total_entries": row.total_entries,
                }
                for row in rows
            ]

    async def list_by_student(self, student_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(DiaryEntry)
                .where(DiaryEntry.student_id == student_id, DiaryEntry.deleted == False)
                .order_by(DiaryEntry.diary_date.desc())
            )

            return [_to_dict(e) for e in result.scalars().all()]

    async def get_by_id(self, entry_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id, DiaryEntry.deleted == False))

            e = result.scalars().first()

            return _to_dict(e) if e else None

    async def create(self, data: dict) -> dict:
        async with self.database.session() as session:
            entry = DiaryEntry(
                id=str(uuid.uuid4()),
                student_id=data.get("student_id"),
                diary_date=date.fromisoformat(data["diary_date"]) if data.get("diary_date") else None,
                teacher_attention=data.get("teacher_attention"),
                followed_agreements=data.get("followed_agreements"),
                activity_interest=data.get("activity_interest"),
                had_lunch=data.get("had_lunch"),
                participated_in_play=data.get("participated_in_play"),
                completed_activities=data.get("completed_activities"),
                bathroom_use=data.get("bathroom_use"),
                open_observation=data.get("open_observation"),
                absence_reason=data.get("absence_reason"),
                teacher_name=data.get("teacher_name"),
                presence=data.get("presence", "Presente"),
                status="active",
                source="manual",
                anonymized_data=_build_diary_anonymized(data),
            )

            session.add(entry)

            await session.commit()

            await session.refresh(entry)

            return _to_dict(entry)

    async def update(self, entry_id: str, data: dict) -> Optional[dict]:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id, DiaryEntry.deleted == False))

            entry = result.scalars().first()

            if not entry:
                return None
            
            for field in [
                "diary_date", "teacher_attention", "followed_agreements", "activity_interest",
                "had_lunch", "participated_in_play", "completed_activities", "bathroom_use",
                "open_observation", "absence_reason", "teacher_name", "presence",
            ]:
                if field in data:
                    value = data[field]
                    if field == "diary_date" and value:
                        value = date.fromisoformat(value)
                    setattr(entry, field, value)

            # Refresh anonymized_data
            entry.anonymized_data = _build_diary_anonymized({
                "student_id": entry.student_id,
                "diary_date": entry.diary_date.isoformat() if entry.diary_date else "",
                "presence": entry.presence,
                "teacher_attention": entry.teacher_attention,
                "followed_agreements": entry.followed_agreements,
                "activity_interest": entry.activity_interest,
                "had_lunch": entry.had_lunch,
                "participated_in_play": entry.participated_in_play,
                "completed_activities": entry.completed_activities,
                "bathroom_use": entry.bathroom_use,
                "open_observation": entry.open_observation,
                "absence_reason": entry.absence_reason,
            })
            await session.commit()

            await session.refresh(entry)

            return _to_dict(entry)

    async def delete(self, entry_id: str) -> bool:
        async with self.database.session() as session:
            result = await session.execute(select(DiaryEntry).where(DiaryEntry.id == entry_id, DiaryEntry.deleted == False))

            entry = result.scalars().first()

            if not entry:
                return False

            entry.deleted = True

            await session.commit()

            return True

    async def get_linked_teachers(self, student_id: str) -> list[str]:
        """Returns list of teacher names linked to the given student."""
        async with self.database.session() as session:
            stmt = (
                select(Teacher.name)
                .join(TeacherStudentLink, Teacher.id == TeacherStudentLink.teacher_id)
                .where(TeacherStudentLink.student_id == student_id)
                .order_by(Teacher.name)
            )

            result = await session.execute(stmt)

            return [row[0] for row in result.all()]

    async def delete_all_for_student(self, student_id: str) -> int:
        async with self.database.session() as session:
            from sqlalchemy import update as sa_update
            result = await session.execute(
                sa_update(DiaryEntry).where(DiaryEntry.student_id == student_id).values(deleted=True)
            )

            await session.commit()

            return result.rowcount

    # ── Image / media helpers ─────────────────────────────────────────────────

    async def add_image(
        self,
        entry_id: str,
        bucket: str,
        object_key: str,
        original_filename: str,
        mime_type: str,
        size_bytes: int,
        public_url: str,
    ) -> dict:
        async with self.database.session() as session:
            record = ObjectStorageFile(
                id=str(uuid.uuid4()),
                doc_type="diary_image",
                reference_id=str(uuid.uuid4()),
                bucket=bucket,
                object_key=object_key,
                original_filename=original_filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                extra={"diary_entry_id": entry_id, "public_url": public_url},
            )

            session.add(record)

            await session.commit()

            await session.refresh(record)

            return self._image_to_dict(record)

    async def list_images(self, entry_id: str) -> list[dict]:
        async with self.database.session() as session:
            result = await session.execute(
                select(ObjectStorageFile).where(
                    ObjectStorageFile.doc_type == "diary_image",
                    ObjectStorageFile.extra["diary_entry_id"].as_string() == entry_id,
                ).order_by(ObjectStorageFile.created_at)
            )

            return [self._image_to_dict(r) for r in result.scalars().all()]

    async def list_images_batch(self, entry_ids: list[str]) -> dict[str, list[dict]]:
        """Return images for multiple diary entries in a single query."""
        if not entry_ids:
            return {}
        async with self.database.session() as session:
            result = await session.execute(
                select(ObjectStorageFile).where(
                    ObjectStorageFile.doc_type == "diary_image",
                    ObjectStorageFile.extra["diary_entry_id"].as_string().in_(entry_ids),
                    ObjectStorageFile.deleted == False,
                ).order_by(ObjectStorageFile.created_at)
            )
            grouped: dict[str, list[dict]] = {eid: [] for eid in entry_ids}
            for row in result.scalars().all():
                eid = (row.extra or {}).get("diary_entry_id")
                if eid in grouped:
                    grouped[eid].append(self._image_to_dict(row))
            return grouped

    async def get_image(self, file_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            obj = await session.get(ObjectStorageFile, file_id)

            if not obj or obj.doc_type != "diary_image":
                return None
            
            return self._image_to_dict(obj)

    async def delete_image(self, file_id: str) -> Optional[dict]:
        async with self.database.session() as session:
            obj = await session.get(ObjectStorageFile, file_id)

            if not obj or obj.doc_type != "diary_image":
                return None
            
            data = self._image_to_dict(obj)

            await session.delete(obj)

            await session.commit()

            return data

    @staticmethod
    def _image_to_dict(r: ObjectStorageFile) -> dict:
        extra = r.extra or {}
        return {
            "id": r.id,
            "diary_entry_id": extra.get("diary_entry_id"),
            "original_filename": r.original_filename,
            "mime_type": r.mime_type,
            "size_bytes": r.size_bytes,
            "public_url": extra.get("public_url"),
            "object_key": r.object_key,
            "bucket": r.bucket,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

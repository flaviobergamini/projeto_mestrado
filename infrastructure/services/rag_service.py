"""RAG service: builds structured JSON, embeds it and persists vectors for
diary entries and case studies. Also provides similarity search."""

import json
import logging
from typing import Optional

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database_context.database import Database
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini
from infrastructure.models.case_study_embedding_gemini import CaseStudyEmbeddingGemini
from infrastructure.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

# ── JSON builders ─────────────────────────────────────────────────────────────

def build_diary_json(entry: dict, student_name: str) -> dict:
    """Returns a compact, categorised dict that represents one diary record."""
    presenca = entry.get("presence") or "Não informado"
    is_present = presenca.lower() == "presente"

    data: dict = {
        "tipo": "registro_diario",
        "data": entry.get("diary_date") or "",
        "aluno_id": entry.get("student_id") or "",
        "aluno_nome": student_name,
        "professor": entry.get("teacher_name") or "",
        "presenca": presenca,
    }

    if is_present:
        data["atividades"] = {
            "lanchou": entry.get("had_lunch") or "",
            "brincadeira_coletiva": entry.get("participated_in_play") or "",
            "atencao_professor": entry.get("teacher_attention") or "",
            "interesse_atividades": entry.get("activity_interest") or "",
            "realizou_atividades": entry.get("completed_activities") or "",
            "uso_banheiro": entry.get("bathroom_use") or "",
            "cumpriu_combinados": entry.get("followed_agreements") or "",
        }
        if entry.get("open_observation"):
            data["observacoes"] = entry["open_observation"]
    else:
        if entry.get("absence_reason"):
            data["motivo_falta"] = entry["absence_reason"]

    return data


def build_case_study_json(case: dict, student_name: str) -> dict:
    """Returns a compact, categorised dict for a case study submission."""
    answers = case.get("answers") or {}

    data: dict = {
        "tipo": "estudo_caso",
        "data": case.get("submitted_at", "")[:10] if case.get("submitted_at") else "",
        "aluno_id": case.get("student_id") or "",
        "aluno_nome": student_name,
        "submetido_por": case.get("submitted_by") or "",
    }

    # Nível de autismo e caracterização geral
    _pick(data, answers, {
        "nivel_autismo": "nivelAutismo",
        "comportamentos": "comportamentos",
        "habilidades": "habilidades",
        "necessidades": "necessidades",
        "estrategias": "estrategias",
        "dificuldades": "dificuldadesAluno",
    })

    # Aspectos socioemocionais (booleanos → textos legíveis)
    social: dict = {}
    _pick_bool(social, answers, {
        "interage_sem_mediacao": "interacts_without_constant_mediation",
        "inicia_interacoes": "initiates_social_interactions_spontaneously",
        "participa_com_estimulos": "participates_with_stimuli",
        "espera_vez": "waits_turn_and_handles_frustration",
        "expressa_emocoes": "expresses_basic_emotions_clearly",
        "reage_elogios": "reacts_positively_to_praise",
        "desregulado_rotina": "emotionally_dysregulated_with_routine_changes",
        "interessa_aprender": "interested_in_learning_new_things",
        "segue_instrucoes": "follows_simple_instructions",
        "mantem_atencao": "maintains_attention_appropriately",
        "resolve_problemas": "solves_simple_problems_independently",
        "aprende_visual": "learns_better_with_visual_support",
    })
    if social:
        data["aspectos_socioemocionais"] = social

    # Aspectos motores
    motor: dict = {}
    _pick_bool(motor, answers, {
        "motora_fina": "fine_motor_coordination",
        "motora_grossa": "gross_motor_coordination",
        "autocuidado": "performs_self_care_independently",
        "comportamentos_repetitivos": "shows_repetitive_motor_behaviors",
    })
    if motor:
        data["aspectos_motores"] = motor

    # Comunicação escola-família
    familia: dict = {}
    _pick_bool(familia, answers, {
        "comunicacao_frequente": "frequent_school_family_communication",
        "apoio_emocional_familia": "family_provides_emotional_support",
        "familia_colabora_terapia": "family_collaboration_in_therapeutic_resources",
        "familia_aberta": "family_open_to_new_approaches",
    })
    _pick(familia, answers, {
        "expectativas_familia": "family_expectations_about_development",
    })
    if familia:
        data["comunicacao_familia_escola"] = familia

    # Adaptações pedagógicas
    _pick(data, answers, {
        "adaptacoes_pedagogicas": "pedagogical_adaptations",
        "desenvolvimento_pedagogico": "pedagogical_development",
    })

    return data


# ── Text serialiser ───────────────────────────────────────────────────────────

def json_to_content(data: dict) -> str:
    """Converts a structured dict to natural-language text for embedding."""
    tipo = data.get("tipo", "")

    if tipo == "registro_diario":
        return _diary_to_text(data)
    if tipo == "estudo_caso":
        return _case_study_to_text(data)
    return json.dumps(data, ensure_ascii=False)


def _diary_to_text(d: dict) -> str:
    lines = [
        f"Registro diário de {d.get('aluno_nome', '')} em {d.get('data', '')}.",
        f"Professor(a): {d.get('professor', 'não informado')}.",
        f"Presença: {d.get('presenca', 'não informado')}.",
    ]
    atividades = d.get("atividades")
    if atividades:
        _LABELS = {
            "lanchou": "Lanchou",
            "brincadeira_coletiva": "Participou de brincadeira coletiva",
            "atencao_professor": "Deu atenção ao professor",
            "interesse_atividades": "Demonstrou interesse nas atividades",
            "realizou_atividades": "Realizou as atividades propostas",
            "uso_banheiro": "Fez uso do banheiro",
            "cumpriu_combinados": "Cumpriu os combinados",
        }
        ativ_parts = [f"{_LABELS.get(k, k)}: {v}" for k, v in atividades.items() if v]
        if ativ_parts:
            lines.append("Atividades: " + "; ".join(ativ_parts) + ".")
    if d.get("observacoes"):
        lines.append(f"Observações: {d['observacoes']}")
    if d.get("motivo_falta"):
        lines.append(f"Motivo da falta: {d['motivo_falta']}")
    return "\n".join(lines)


def _case_study_to_text(d: dict) -> str:
    lines = [
        f"Estudo de caso de {d.get('aluno_nome', '')} ({d.get('data', '')}).",
        f"Submetido por: {d.get('submetido_por', 'não informado')}.",
    ]
    if d.get("nivel_autismo"):
        lines.append(f"Nível do autismo: {d['nivel_autismo']}.")
    for key, label in [
        ("comportamentos", "Comportamentos"),
        ("habilidades", "Habilidades"),
        ("necessidades", "Necessidades"),
        ("estrategias", "Estratégias"),
        ("dificuldades", "Dificuldades"),
        ("adaptacoes_pedagogicas", "Adaptações pedagógicas"),
        ("desenvolvimento_pedagogico", "Desenvolvimento pedagógico"),
    ]:
        if d.get(key):
            lines.append(f"{label}: {d[key]}")
    social = d.get("aspectos_socioemocionais", {})
    if social:
        positivos = [k for k, v in social.items() if v is True]
        negativos = [k for k, v in social.items() if v is False]
        if positivos:
            lines.append(f"Pontos positivos socioemocionais: {', '.join(positivos)}.")
        if negativos:
            lines.append(f"Aspectos socioemocionais a desenvolver: {', '.join(negativos)}.")
    familia = d.get("comunicacao_familia_escola", {})
    if familia:
        lines.append(f"Comunicação escola-família: {json.dumps(familia, ensure_ascii=False)}")
    return "\n".join(lines)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pick(target: dict, source: dict, mapping: dict) -> None:
    for dest, src in mapping.items():
        v = source.get(src)
        if v not in (None, "", [], {}):
            target[dest] = v


def _pick_bool(target: dict, source: dict, mapping: dict) -> None:
    for dest, src in mapping.items():
        v = source.get(src)
        if v is not None:
            target[dest] = bool(v)


# ── RagService ────────────────────────────────────────────────────────────────

class RagService:
    def __init__(self, database: Database, gemini: GeminiService):
        self._db = database
        self._gemini = gemini

    # ── embed & save ──────────────────────────────────────────────────────────

    async def embed_diary_entry(
        self,
        entry: dict,
        student_name: str,
    ) -> None:
        """Build JSON + embed + upsert into diary_embedding_gemini."""
        entry_id = entry.get("id")
        student_id = entry.get("student_id")
        if not entry_id:
            return

        structured = build_diary_json(entry, student_name)
        content = json_to_content(structured)

        try:
            vector = self._gemini.generate_embedding(content)
        except Exception:
            logger.exception("Gemini embedding failed for diary entry %s", entry_id)
            return

        async with self._db.session() as session:
            # Delete previous embedding for this entry (upsert behaviour)
            await session.execute(
                delete(DiaryEmbeddingGemini)
                .where(DiaryEmbeddingGemini.diary_entry_id == entry_id)
            )
            row = DiaryEmbeddingGemini(
                diary_entry_id=entry_id,
                student_id=student_id,
                content=content,
                meta_data=structured,
                embedding=vector,
            )
            session.add(row)
            await session.commit()

    async def embed_case_study(
        self,
        case: dict,
        student_name: str,
    ) -> None:
        """Build JSON + embed + upsert into case_study_embedding_gemini."""
        case_id = case.get("id")
        student_id = case.get("student_id")
        if not case_id:
            return

        structured = build_case_study_json(case, student_name)
        content = json_to_content(structured)

        try:
            vector = self._gemini.generate_embedding(content)
        except Exception:
            logger.exception("Gemini embedding failed for case study %s", case_id)
            return

        async with self._db.session() as session:
            await session.execute(
                delete(CaseStudyEmbeddingGemini)
                .where(CaseStudyEmbeddingGemini.case_study_id == case_id)
            )
            row = CaseStudyEmbeddingGemini(
                case_study_id=case_id,
                student_id=student_id,
                content=content,
                meta_data=structured,
                embedding=vector,
            )
            session.add(row)
            await session.commit()

    # ── search ────────────────────────────────────────────────────────────────

    async def search(
        self,
        query: str,
        student_id: str,
        limit: int = 5,
    ) -> list[dict]:
        """Return the most semantically similar chunks for the given student."""
        try:
            query_vector = self._gemini.generate_embedding(query)
        except Exception:
            logger.exception("Gemini embedding failed for query")
            return []

        vector_literal = f"[{','.join(str(x) for x in query_vector)}]"

        async with self._db.session() as session:
            # Cosine similarity search across both tables, union-ed
            sql = text("""
                SELECT content, meta_data::text AS meta_json,
                       (embedding <=> CAST(:vec AS vector)) AS distance,
                       'diario' AS source
                FROM diary_embedding_gemini
                WHERE student_id = :sid
                UNION ALL
                SELECT content, meta_data::text AS meta_json,
                       (embedding <=> CAST(:vec AS vector)) AS distance,
                       'estudo_caso' AS source
                FROM case_study_embedding_gemini
                WHERE student_id = :sid
                ORDER BY distance ASC
                LIMIT :lim
            """)
            result = await session.execute(
                sql,
                {"vec": vector_literal, "sid": student_id, "lim": limit},
            )
            rows = result.fetchall()

        chunks = []
        for row in rows:
            meta = {}
            try:
                meta = json.loads(row.meta_json) if row.meta_json else {}
            except Exception:
                pass
            chunks.append({
                "content": row.content,
                "source": row.source,
                "distance": float(row.distance),
                "meta": meta,
            })
        return chunks

    async def build_rag_context(
        self,
        query: str,
        student_id: str,
        student_name: str,
        limit: int = 5,
    ) -> str:
        """Returns a ready-to-use context string for the LLM prompt."""
        chunks = await self.search(query, student_id, limit=limit)
        if not chunks:
            return f"Não há registros vetorizados para {student_name} ainda."

        lines = [f"Informações relevantes sobre {student_name} (recuperadas por similaridade semântica):"]
        for i, chunk in enumerate(chunks, 1):
            source_label = "Diário" if chunk["source"] == "diario" else "Estudo de Caso"
            lines.append(f"\n[{i}] {source_label}")
            lines.append(chunk["content"])
        return "\n".join(lines)

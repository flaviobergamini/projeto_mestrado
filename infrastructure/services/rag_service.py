"""RAG service: builds structured JSON, embeds it and persists vectors for
diary entries and case studies. Also provides similarity search."""

import asyncio
import json
import logging
from typing import Optional

from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database_context.database import Database
from infrastructure.models.diary_embedding_gemini import DiaryEmbeddingGemini
from infrastructure.models.case_study_embedding_gemini import CaseStudyEmbeddingGemini
from infrastructure.services.gemini_service import GeminiService
from infrastructure.repositories.ai_usage_repository import AiUsageRepository

logger = logging.getLogger(__name__)

# ── JSON builders ─────────────────────────────────────────────────────────────

def build_diary_json(entry: dict) -> dict:
    """Returns a compact, anonymised dict for one diary record (no PII)."""
    presenca = entry.get("presence") or "Não informado"
    is_present = presenca.lower() == "presente"

    data: dict = {
        "tipo": "registro_diario",
        "data": entry.get("diary_date") or "",
        "aluno_id": entry.get("student_id") or "",
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


def build_case_study_json(case: dict) -> dict:
    """Returns a compact, anonymised dict for a case study (no PII)."""
    answers = case.get("answers") or {}

    data: dict = {
        "tipo": "estudo_caso",
        "data": case.get("submitted_at", "")[:10] if case.get("submitted_at") else "",
        "aluno_id": case.get("student_id") or "",
    }

    # Non-PII cadastral fields only (exclude studentName, schoolName, mainTeacher, supportTeacher)
    _pick(data, answers, {
        "idade_aluno": "studentAge",
        "ano_escolar": "schoolYear",
        "turma": "className",
    })

    # Informações pessoais (texto livre)
    _pick(data, answers, {
        "atividades_favoritas": "favoriteActivities",
        "tarefas_dificeis": "difficultTasks",
        "expressa_necessidades": "expressNeeds",
        "interesses_especiais": "specialInterests",
        "apoios_disponiveis": "schoolSupports",
        "apoios_desejados": "desiredSupports",
    })

    # Aspectos social + afetivo + cognitivo (Sim/Não → texto)
    social: dict = {}
    _pick_simno(social, answers, {
        "interage_sem_mediacao": "socialInteracts",
        "inicia_interacoes": "socialInitiates",
        "participa_atividades": "socialParticipates",
        "espera_vez": "socialWaitsTurn",
        "compartilha_experiencias": "socialShares",
        "expressa_emocoes": "affectiveDemonstrates",
        "reage_elogios": "affectiveReacts",
        "busca_apoio": "affectiveSeeksSupport",
        "desregulado_rotina": "affectiveRoutineChanges",
        "consegue_se_acalmar": "affectiveCalmDown",
        "interesse_aprender": "cognitiveInterest",
        "segue_instrucoes": "cognitiveInstructions",
        "mantem_atencao": "cognitiveAttention",
        "resolve_problemas": "cognitiveProblems",
        "aprende_visual": "cognitiveVisual",
    })
    if social:
        data["aspectos_socioemocionais"] = social

    # Aspectos motores
    motor: dict = {}
    _pick_simno(motor, answers, {
        "motora_fina": "motorFine",
        "motora_grossa": "motorGross",
        "autocuidado": "motorSelfCare",
        "atividades_fisicas": "motorPhysical",
        "comportamentos_repetitivos": "motorRepetitive",
    })
    if motor:
        data["aspectos_motores"] = motor

    # Alimentação
    alimentacao: dict = {}
    _pick_simno(alimentacao, answers, {
        "repertorio_restrito": "feedingRestricted",
        "precisa_auxilio": "feedingNeedsHelp",
        "incomodo_mistura": "feedingMixedFoods",
        "prefere_silencio": "feedingQuietPlace",
        "comportamentos_desafiadores": "feedingChallenging",
    })
    _pick(alimentacao, answers, {"observacoes": "feedingObs"})
    if alimentacao:
        data["alimentacao"] = alimentacao

    # Comunicação escola-família
    familia: dict = {}
    _pick_simno(familia, answers, {
        "familia_participa": "familyParticipates",
        "comunicacao_frequente": "familyCommunication",
        "apoio_emocional": "familySupport",
        "colaboracao_terapia": "familyCollaboration",
        "aberta_novas_abordagens": "familyOpenness",
    })
    _pick(familia, answers, {
        "expectativas_familia": "familyExpectations",
        "envolvimento_familia": "familyInvolvement",
        "consciencia_direitos": "familyAwareness",
    })
    if familia:
        data["comunicacao_familia_escola"] = familia

    # Escola
    escola: dict = {}
    _pick(escola, answers, {
        "necessidades_especificas": "specificNeeds",
        "habilidades_potencialidades": "studentSkills",
        "atendimentos_recebidos": "receivesSupport",
        "recursos_acessibilidade": "accessibilityResources",
        "avaliacao_desempenho": "performanceEvaluation",
    })
    if escola:
        data["informacoes_escola"] = escola

    # Adaptações pedagógicas
    _pick(data, answers, {
        "adaptacoes_pedagogicas": "pedagogicalAdaptations",
        "desenvolvimento_pedagogico": "pedagogicalDevelopment",
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
        f"Registro diário (aluno {d.get('aluno_id', '')}) em {d.get('data', '')}.",
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

    # Normalized observation — preferred over raw text when available
    obs_norm = d.get("observacoes_normalizadas")
    if obs_norm and isinstance(obs_norm, dict):
        if obs_norm.get("resumo"):
            lines.append(f"Resumo das observações: {obs_norm['resumo']}")
        for field, label in [
            ("comportamentos_observados", "Comportamentos observados"),
            ("habilidades_demonstradas", "Habilidades demonstradas"),
            ("dificuldades_identificadas", "Dificuldades identificadas"),
            ("recomendacoes", "Recomendações"),
        ]:
            items = obs_norm.get(field) or []
            if items:
                lines.append(f"{label}: {', '.join(items)}.")
    elif d.get("observacoes"):
        lines.append(f"Observações: {d['observacoes']}")

    if d.get("motivo_falta"):
        lines.append(f"Motivo da falta: {d['motivo_falta']}")
    return "\n".join(lines)


def _case_study_to_text(d: dict) -> str:
    lines = [
        f"Estudo de caso (aluno {d.get('aluno_id', '')}) em {d.get('data', '')}.",
    ]
    if d.get("idade_aluno"):
        lines.append(f"Idade: {d['idade_aluno']} anos.")
    if d.get("ano_escolar"):
        lines.append(f"Ano escolar: {d['ano_escolar']} - Turma {d.get('turma', '')}.")

    for key, label in [
        ("atividades_favoritas", "Atividades favoritas"),
        ("tarefas_dificeis", "Tarefas difíceis"),
        ("expressa_necessidades", "Expressão de necessidades"),
        ("interesses_especiais", "Interesses especiais"),
        ("apoios_disponiveis", "Apoios disponíveis"),
        ("apoios_desejados", "Apoios desejados"),
        ("necessidades_especificas", "Necessidades específicas"),
        ("habilidades_potencialidades", "Habilidades e potencialidades"),
        ("atendimentos_recebidos", "Atendimentos recebidos"),
        ("recursos_acessibilidade", "Recursos de acessibilidade"),
        ("avaliacao_desempenho", "Avaliação de desempenho"),
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
            lines.append(f"Aspectos a desenvolver: {', '.join(negativos)}.")

    motor = d.get("aspectos_motores", {})
    if motor:
        positivos = [k for k, v in motor.items() if v is True]
        negativos = [k for k, v in motor.items() if v is False]
        if positivos:
            lines.append(f"Aspectos motores positivos: {', '.join(positivos)}.")
        if negativos:
            lines.append(f"Aspectos motores a desenvolver: {', '.join(negativos)}.")

    alimentacao = d.get("alimentacao", {})
    if alimentacao:
        lines.append(f"Alimentação: {json.dumps(alimentacao, ensure_ascii=False)}")

    familia = d.get("comunicacao_familia_escola", {})
    if familia:
        if "expectativas_familia" in familia:
            lines.append(f"Expectativas da família: {familia['expectativas_familia']}")
        bool_familia = {k: v for k, v in familia.items() if isinstance(v, bool)}
        if bool_familia:
            lines.append(f"Comunicação escola-família: {json.dumps(bool_familia, ensure_ascii=False)}")

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


def _pick_simno(target: dict, source: dict, mapping: dict) -> None:
    """Maps 'Sim'/'Não' string answers to True/False booleans."""
    for dest, src in mapping.items():
        v = source.get(src)
        if v in ("Sim", "Não"):
            target[dest] = v == "Sim"


# ── RagService ────────────────────────────────────────────────────────────────

class RagService:
    def __init__(self, database: Database, gemini: GeminiService, usage_repo: Optional[AiUsageRepository] = None, diary_repo=None):
        self._db = database
        self._gemini = gemini
        self._usage = usage_repo
        self._diary_repo = diary_repo  # DiaryRepository — injected for persisting normalized_observation

    # ── embed & save ──────────────────────────────────────────────────────────

    async def embed_diary_entry(
        self,
        entry: dict,
    ) -> None:
        """Build anonymised JSON + normalize observation + embed + upsert into diary_embedding_gemini."""
        entry_id = entry.get("id")
        student_id = entry.get("student_id")
        if not entry_id:
            return

        structured = build_diary_json(entry)

        # Normalize open_observation with Gemini, persist to DB, then use in embedding
        raw_obs = entry.get("open_observation") or ""
        # Prefer already-persisted normalization to avoid re-processing
        obs_normalized = entry.get("normalized_observation")
        if not obs_normalized and raw_obs.strip():
            try:
                obs_normalized, obs_usage = await asyncio.to_thread(
                    self._gemini.normalize_diary_observation, raw_obs
                )
                if self._usage:
                    await self._usage.log(
                        model=obs_usage.model,
                        operation="normalize_diary_observation",
                        input_tokens=obs_usage.input_tokens,
                        output_tokens=obs_usage.output_tokens,
                        total_tokens=obs_usage.total_tokens,
                        duration_ms=obs_usage.duration_ms,
                    )
                # Persist so all future AI features read from the stored JSON
                if self._diary_repo and obs_normalized:
                    await self._diary_repo.save_normalized_observation(entry_id, obs_normalized)
            except Exception:
                logger.warning("Observation normalization failed for entry %s — using raw text", entry_id)
        if obs_normalized:
            structured["observacoes_normalizadas"] = obs_normalized

        content = json_to_content(structured)

        try:
            vector, usage = await asyncio.to_thread(self._gemini.generate_embedding_tracked, content)
            if self._usage:
                await self._usage.log(model=usage.model, operation="embedding_diary",
                                      input_tokens=usage.input_tokens, output_tokens=0,
                                      total_tokens=usage.total_tokens, duration_ms=usage.duration_ms)
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
    ) -> None:
        """Build anonymised JSON + embed + upsert into case_study_embedding_gemini."""
        case_id = case.get("id")
        student_id = case.get("student_id")
        if not case_id:
            return

        structured = build_case_study_json(case)
        content = json_to_content(structured)

        try:
            vector, usage = await asyncio.to_thread(self._gemini.generate_embedding_tracked, content)
            if self._usage:
                await self._usage.log(model=usage.model, operation="embedding_case_study",
                                      input_tokens=usage.input_tokens, output_tokens=0,
                                      total_tokens=usage.total_tokens, duration_ms=usage.duration_ms)
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

    VALID_SOURCES = {"diary", "case_study", "family_diary", "therapy_diary"}

    async def get_sources_preview(self, student_id: str) -> dict:
        """Return available source counts for a student."""
        async with self._db.session() as session:
            diary_result = await session.execute(
                text("SELECT COUNT(*) FROM diary_embedding_gemini WHERE student_id = :sid"),
                {"sid": student_id},
            )
            diary_count = int(diary_result.scalar() or 0)

            case_result = await session.execute(
                text("SELECT COUNT(*) FROM case_study_embedding_gemini WHERE student_id = :sid"),
                {"sid": student_id},
            )
            case_count = int(case_result.scalar() or 0)

            student_result = await session.execute(
                text("SELECT id, school_id FROM students WHERE id = :sid AND deleted = false"),
                {"sid": student_id},
            )
            student_row = student_result.fetchone()
            school_id = student_row.school_id if student_row else None

            teacher_result = await session.execute(
                text("SELECT COUNT(*) FROM teacher_student_links WHERE student_id = :sid AND deleted = false"),
                {"sid": student_id},
            )
            teacher_count = int(teacher_result.scalar() or 0)

            pdi_result = await session.execute(
                text("SELECT COUNT(*) FROM pdis WHERE student_id = :sid AND deleted = false"),
                {"sid": student_id},
            )
            pdi_count = int(pdi_result.scalar() or 0)

            gpei_result = await session.execute(
                text("SELECT COUNT(*) FROM generated_peis WHERE student_id = :sid AND deleted = false"),
                {"sid": student_id},
            )
            gpei_count = int(gpei_result.scalar() or 0)

            family_result = await session.execute(
                text("SELECT COUNT(*) FROM diary_entries WHERE student_id = :sid AND source = 'family' AND deleted = false"),
                {"sid": student_id},
            )
            family_count = int(family_result.scalar() or 0)

            therapy_result = await session.execute(
                text("SELECT COUNT(*) FROM diary_entries WHERE student_id = :sid AND source = 'therapy' AND deleted = false"),
                {"sid": student_id},
            )
            therapy_count = int(therapy_result.scalar() or 0)

            kanban_result = await session.execute(
                text("SELECT COUNT(*) FROM pei_kanban_cards WHERE student_id = :sid AND deleted = false"),
                {"sid": student_id},
            )
            kanban_count = int(kanban_result.scalar() or 0)

        return {
            "student": {"available": student_row is not None, "count": 1 if student_row else 0},
            "diary": {"available": diary_count > 0, "count": diary_count},
            "family_diary": {"available": family_count > 0, "count": family_count},
            "therapy_diary": {"available": therapy_count > 0, "count": therapy_count},
            "case_study": {"available": case_count > 0, "count": case_count},
            "school": {"available": school_id is not None, "count": 1 if school_id else 0},
            "teacher": {"available": teacher_count > 0, "count": teacher_count},
            "pdi": {"available": pdi_count > 0, "count": pdi_count},
            "generated_pei": {"available": gpei_count > 0, "count": gpei_count},
            "kanban_progress": {"available": kanban_count > 0, "count": kanban_count},
        }

    @staticmethod
    def _fts_query(query: str) -> str:
        """Sanitize query string for plainto_tsquery."""
        return " ".join(query.split())

    async def search(
        self,
        query: str,
        student_id: str,
        limit: int = 20,
        sources: Optional[list[str]] = None,
        max_distance: float = 0.5,
    ) -> list[dict]:
        """Hybrid search: vector similarity + full-text search (tsvector), merged and deduplicated.

        sources: subset of ['diary', 'case_study']. Defaults to both when None or empty.
        max_distance: cosine distance threshold — chunks above this are discarded from vector results.
        """
        active = set(sources) & self.VALID_SOURCES if sources else self.VALID_SOURCES
        if not active:
            return []

        try:
            query_vector, emb_usage = await asyncio.to_thread(self._gemini.generate_embedding_tracked, query)
            if self._usage:
                await self._usage.log(model=emb_usage.model, operation="embedding_search",
                                      input_tokens=emb_usage.input_tokens, output_tokens=0,
                                      total_tokens=emb_usage.total_tokens, duration_ms=emb_usage.duration_ms)
        except Exception:
            logger.exception("Gemini embedding failed for query")
            return []

        vector_literal = f"[{','.join(str(x) for x in query_vector)}]"
        fts_query = self._fts_query(query)

        # ── Vector search ─────────────────────────────────────────────────────
        vec_parts = []
        if active & {"diary", "family_diary", "therapy_diary"}:
            vec_parts.append(
                "SELECT id, content, meta_data::text AS meta_json,"
                " (embedding <=> CAST(:vec AS vector)) AS distance,"
                " 'diario' AS source"
                " FROM diary_embedding_gemini WHERE student_id = :sid"
                " AND (embedding <=> CAST(:vec AS vector)) < :max_dist"
            )
        if "case_study" in active:
            vec_parts.append(
                "SELECT id, content, meta_data::text AS meta_json,"
                " (embedding <=> CAST(:vec AS vector)) AS distance,"
                " 'estudo_caso' AS source"
                " FROM case_study_embedding_gemini WHERE student_id = :sid"
                " AND (embedding <=> CAST(:vec AS vector)) < :max_dist"
            )

        # ── Keyword search (FTS) ──────────────────────────────────────────────
        kw_parts = []
        if active & {"diary", "family_diary", "therapy_diary"}:
            kw_parts.append(
                "SELECT id, content, meta_data::text AS meta_json,"
                " 0.0 AS distance,"
                " 'diario' AS source"
                " FROM diary_embedding_gemini WHERE student_id = :sid"
                " AND to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', :fts)"
            )
        if "case_study" in active:
            kw_parts.append(
                "SELECT id, content, meta_data::text AS meta_json,"
                " 0.0 AS distance,"
                " 'estudo_caso' AS source"
                " FROM case_study_embedding_gemini WHERE student_id = :sid"
                " AND to_tsvector('portuguese', content) @@ plainto_tsquery('portuguese', :fts)"
            )

        async with self._db.session() as session:
            vec_rows, kw_rows = [], []

            if vec_parts:
                vec_sql = " UNION ALL ".join(vec_parts) + " ORDER BY distance ASC LIMIT :lim"
                res = await session.execute(
                    text(vec_sql),
                    {"vec": vector_literal, "sid": student_id, "lim": limit, "max_dist": max_distance},
                )
                vec_rows = res.fetchall()

            if kw_parts:
                # Sem LIMIT: keyword search já está filtrada por student_id,
                # então o volume é limitado ao histórico do aluno (seguro).
                kw_sql = " UNION ALL ".join(kw_parts)
                try:
                    res = await session.execute(
                        text(kw_sql),
                        {"sid": student_id, "fts": fts_query},
                    )
                    kw_rows = res.fetchall()
                except Exception:
                    # plainto_tsquery pode falhar com queries muito curtas ou inválidas
                    kw_rows = []

        # ── Merge + deduplicate (vector first, keyword appended) ──────────────
        seen: set = set()
        chunks: list[dict] = []

        for row in vec_rows:
            key = (row.source, row.id)
            if key not in seen:
                seen.add(key)
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
                    "match_type": "vector",
                })

        for row in kw_rows:
            key = (row.source, row.id)
            if key not in seen:
                seen.add(key)
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
                    "match_type": "keyword",
                })

        return chunks[:limit]

    async def build_rag_context(
        self,
        query: str,
        student_id: str,
        limit: int = 20,
        sources: Optional[list[str]] = None,
        max_distance: float = 0.5,
    ) -> str:
        """Returns a ready-to-use anonymised context string for the LLM prompt."""
        chunks = await self.search(query, student_id, limit=limit, sources=sources, max_distance=max_distance)
        if not chunks:
            return "Não há registros vetorizados para este aluno ainda."

        lines = [f"Registros relevantes (aluno {student_id}, recuperados por similaridade semântica):"]
        for i, chunk in enumerate(chunks, 1):
            source_label = "Diário" if chunk["source"] == "diario" else "Estudo de Caso"
            lines.append(f"\n[{i}] {source_label}")
            lines.append(chunk["content"])
        return "\n".join(lines)

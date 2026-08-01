import time
import logging
import google.ai.generativelanguage_v1beta as glm
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768


class UsageData:
    """Token usage and timing for a single Gemini API call."""
    __slots__ = ("model", "input_tokens", "output_tokens", "total_tokens", "duration_ms")

    def __init__(self, model: str, input_tokens: int, output_tokens: int, total_tokens: int, duration_ms: int):
        self.model = model
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens
        self.duration_ms = duration_ms


class GeminiService:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL or "models/gemini-embedding-001"
        self.api_key = settings.GEMINI_API_KEY

        self._llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.3,
        )
        self._embed_client = glm.GenerativeServiceClient(
            client_options={"api_key": self.api_key}
        )

    # ── Text generation ──────────────────────────────────────────────────────

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generate text — returns only the string (backwards-compatible)."""
        text, _ = self.generate_text_tracked(prompt, system_instruction)
        return text

    def generate_text_tracked(self, prompt: str, system_instruction: str | None = None) -> tuple[str, UsageData]:
        """Generate text and return (text, UsageData) for usage tracking."""
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))

        t0 = time.monotonic()
        response = self._llm.invoke(messages)
        duration_ms = int((time.monotonic() - t0) * 1000)

        meta = getattr(response, "usage_metadata", None) or {}
        input_tok = int(meta.get("input_tokens", 0))
        output_tok = int(meta.get("output_tokens", 0))
        total_tok = int(meta.get("total_tokens", 0)) or (input_tok + output_tok)

        usage = UsageData(
            model=self.model_name,
            input_tokens=input_tok,
            output_tokens=output_tok,
            total_tokens=total_tok,
            duration_ms=duration_ms,
        )
        return response.content, usage

    # ── Embeddings ───────────────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding — returns only the vector (backwards-compatible)."""
        vector, _ = self.generate_embedding_tracked(text)
        return vector

    def generate_embedding_tracked(self, text: str) -> tuple[list[float], UsageData]:
        """Generate embedding and return (vector, UsageData) for usage tracking."""
        req = glm.EmbedContentRequest(
            model=self.embedding_model_name,
            content=glm.Content(parts=[glm.Part(text=text)]),
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )
        t0 = time.monotonic()
        resp = self._embed_client.embed_content(req)
        duration_ms = int((time.monotonic() - t0) * 1000)

        # Embedding API doesn't directly return token count; approximate from char length
        approx_tokens = max(1, len(text) // 4)

        usage = UsageData(
            model=self.embedding_model_name,
            input_tokens=approx_tokens,
            output_tokens=0,
            total_tokens=approx_tokens,
            duration_ms=duration_ms,
        )
        return list(resp.embedding.values), usage

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.generate_embedding(t) for t in texts]

    # ── Diary normalization ──────────────────────────────────────────────────

    def normalize_diary_observation(self, text: str) -> tuple[dict, UsageData]:
        """Send raw open_observation text to Gemini and return a structured summary dict.

        Returns a dict with keys: resumo, comportamentos_observados,
        habilidades_demonstradas, dificuldades_identificadas, recomendacoes.
        Falls back to {"resumo": text} on any parse failure.
        """
        import json, re

        prompt = f"""Você é um assistente especializado em educação inclusiva para alunos com TEA (Transtorno do Espectro Autista).

Analise a seguinte observação livre escrita por um professor e normalize-a em um JSON estruturado.

OBSERVAÇÃO:
{text}

Retorne APENAS o JSON abaixo preenchido, sem explicações, sem markdown, sem ```json:

{{
  "resumo": "<resumo objetivo em 1-2 frases>",
  "comportamentos_observados": ["<lista de comportamentos mencionados ou inferidos>"],
  "habilidades_demonstradas": ["<habilidades positivas observadas>"],
  "dificuldades_identificadas": ["<dificuldades ou desafios mencionados>"],
  "recomendacoes": ["<sugestões ou encaminhamentos mencionados pelo professor>"]
}}

Se alguma categoria não tiver informações, use lista vazia [].
Não invente informações que não estejam na observação original."""

        messages = [HumanMessage(content=prompt)]
        t0 = time.monotonic()
        response = self._llm.invoke(messages)
        duration_ms = int((time.monotonic() - t0) * 1000)

        raw = response.content.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

        meta = getattr(response, "usage_metadata", None) or {}
        usage = UsageData(
            model=self.model_name,
            input_tokens=int(meta.get("input_tokens", 0)),
            output_tokens=int(meta.get("output_tokens", 0)),
            total_tokens=int(meta.get("total_tokens", 0)),
            duration_ms=duration_ms,
        )

        try:
            normalized = json.loads(raw)
        except Exception:
            normalized = {"resumo": text}

        return normalized, usage

    # ── Audio transcription ──────────────────────────────────────────────────

    def transcribe_diary_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> dict:
        """Send audio to Gemini and extract structured diary fields.

        Returns a dict with the same keys as DiaryEntryCreate (minus student_id/diary_date).
        All answer fields use 'Sim' | 'Não' | 'Parcialmente' | null.
        """
        import base64

        prompt = """Você é um assistente que ajuda professores a registrar o diário de acompanhamento de alunos com TEA.

Ouça o áudio e preencha o JSON abaixo com base no que o professor relatou.

Regras:
- Para os campos de atividade use SOMENTE: "Sim", "Não", "Parcialmente" ou null (se não mencionado).
- Para "presence" use SOMENTE: "Presente", "Falta Justificada" ou "Falta Injustificada".
- "open_observation": texto livre com observações adicionais mencionadas, ou null.
- "absence_reason": motivo da falta se for Falta Justificada, ou null.
- Não invente informações que não foram ditas no áudio. Use null para campos não mencionados.

Retorne APENAS o JSON, sem explicações, sem markdown, sem ```json.

{
  "presence": "Presente",
  "teacher_attention": null,
  "followed_agreements": null,
  "activity_interest": null,
  "had_lunch": null,
  "participated_in_play": null,
  "completed_activities": null,
  "bathroom_use": null,
  "open_observation": null,
  "absence_reason": null
}"""

        message = HumanMessage(content=[
            {
                "type": "media",
                "data": base64.b64encode(audio_bytes).decode("utf-8"),
                "mime_type": mime_type,
            },
            {"type": "text", "text": prompt},
        ])

        t0 = time.monotonic()
        response = self._llm.invoke([message])
        duration_ms = int((time.monotonic() - t0) * 1000)

        import json, re
        raw = response.content.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

        meta = getattr(response, "usage_metadata", None) or {}
        usage = UsageData(
            model=self.model_name,
            input_tokens=int(meta.get("input_tokens", 0)),
            output_tokens=int(meta.get("output_tokens", 0)),
            total_tokens=int(meta.get("total_tokens", 0)),
            duration_ms=duration_ms,
        )

        try:
            fields = json.loads(raw)
        except Exception:
            fields = {}

        return fields, usage

    def transcribe_audio_verbatim(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> tuple[str, "UsageData"]:
        """Transcreve o áudio fielmente, sem resumir. Retorna o texto e os dados de uso."""
        import base64, time as _time

        prompt = """Transcreva exatamente o que foi dito no áudio, em português, sem resumir, sem interpretar, sem adicionar ou omitir nenhuma informação. Retorne apenas o texto transcrito, sem títulos, sem explicações adicionais."""

        message = HumanMessage(content=[
            {
                "type": "media",
                "data": base64.b64encode(audio_bytes).decode("utf-8"),
                "mime_type": mime_type,
            },
            {"type": "text", "text": prompt},
        ])

        t0 = _time.monotonic()
        response = self._llm.invoke([message])
        duration_ms = int((_time.monotonic() - t0) * 1000)

        meta = getattr(response, "usage_metadata", None) or {}
        usage = UsageData(
            model=self.model_name,
            input_tokens=int(meta.get("input_tokens", 0)),
            output_tokens=int(meta.get("output_tokens", 0)),
            total_tokens=int(meta.get("total_tokens", 0)),
            duration_ms=duration_ms,
        )

        return response.content.strip(), usage

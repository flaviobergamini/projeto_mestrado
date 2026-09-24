import time
import logging
from google import genai
from google.genai import types
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


def _usage_from_metadata(model: str, meta, duration_ms: int, fallback_text: str = "") -> UsageData:
    """Maps google-genai's usage_metadata (prompt/candidates/total_token_count) to UsageData,
    com fallback por estimativa de caracteres quando o campo vem ausente (mesmo padrão da PoC)."""
    input_tok = getattr(meta, "prompt_token_count", None) if meta else None
    output_tok = getattr(meta, "candidates_token_count", None) if meta else None
    total_tok = getattr(meta, "total_token_count", None) if meta else None

    if input_tok is None:
        input_tok = max(1, len(fallback_text) // 4) if fallback_text else 0
    if total_tok is None:
        total_tok = input_tok + (output_tok or 0)
    if output_tok is None:
        output_tok = max(0, total_tok - input_tok)

    return UsageData(
        model=model,
        input_tokens=max(0, int(input_tok)),
        output_tokens=max(0, int(output_tok)),
        total_tokens=max(0, int(total_tok)),
        duration_ms=duration_ms,
    )


class GeminiService:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
        self.embedding_model_name = settings.GEMINI_EMBEDDING_MODEL or "models/gemini-embedding-001"
        self.api_key = settings.GEMINI_API_KEY

    # ── Text generation ──────────────────────────────────────────────────────

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        """Generate text — returns only the string (backwards-compatible)."""
        text, _ = self.generate_text_tracked(prompt, system_instruction)
        return text

    def generate_text_tracked(self, prompt: str, system_instruction: str | None = None) -> tuple[str, UsageData]:
        """Generate text and return (text, UsageData) for usage tracking.

        Usa o SDK unificado google-genai (mesmo usado na PoC) em vez do
        langchain_google_genai.ChatGoogleGenerativeAI — o cliente antigo travava
        silenciosamente em algumas chamadas, sem respeitar nenhum timeout próprio.
        Um client novo por chamada evita reaproveitar uma conexão que possa ter
        ficado em estado ruim (mesma causa raiz já vista no client HTTP persistente
        de download de imagens de diário).

        max_output_tokens e temperature>0 mitigam um loop de repetição observado
        na prática: com contexto muito grande (ex.: aluno com 300+ registros de
        diário) e temperature=0.0 (decodificação gulosa), o Gemini às vezes entra
        num loop gerando só espaços em branco até bater no teto absoluto de
        tokens do modelo (~65k) — um PEI de ~1,8 milhão de caracteres, só
        espaços, em vez de travar ou responder normalmente.

        O 2.5 Flash é um modelo de raciocínio híbrido — os tokens de "pensamento"
        saem do MESMO orçamento de max_output_tokens que o texto final, então um
        teto baixo (testado: 8000) cortava o PEI no meio depois de gastar quase
        tudo pensando. thinking_budget limita só o raciocínio (4000 tokens é de
        sobra pra sintetizar o contexto), sobrando 20000 pro texto visível —
        bem mais que um PEI real precisa (~5000 tokens) mas bem abaixo do teto
        absoluto que alimentava o loop de repetição.
        """
        client = genai.Client(api_key=self.api_key)
        thinking_config = types.ThinkingConfig(thinking_budget=3000)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            max_output_tokens=14000,
            thinking_config=thinking_config,
        ) if system_instruction else types.GenerateContentConfig(
            temperature=0.2, max_output_tokens=14000, thinking_config=thinking_config,
        )

        t0 = time.monotonic()
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config,
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

        usage = _usage_from_metadata(self.model_name, getattr(response, "usage_metadata", None), duration_ms, prompt)
        text = response.text
        if not text or not text.strip():
            # Resposta vazia (bloqueio de segurança, orçamento de tokens gasto só
            # pensando, etc.) — falha explícita em vez de devolver None adiante.
            candidates = getattr(response, "candidates", None) or []
            reason = getattr(candidates[0], "finish_reason", None) if candidates else None
            raise ValueError(f"Gemini retornou resposta vazia (finish_reason={reason})")
        return text, usage

    # ── Embeddings ───────────────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding — returns only the vector (backwards-compatible)."""
        vector, _ = self.generate_embedding_tracked(text)
        return vector

    def generate_embedding_tracked(self, text: str) -> tuple[list[float], UsageData]:
        """Generate embedding and return (vector, UsageData) for usage tracking."""
        client = genai.Client(api_key=self.api_key)

        t0 = time.monotonic()
        result = client.models.embed_content(
            model=self.embedding_model_name,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS),
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

        usage = _usage_from_metadata(self.embedding_model_name, getattr(result, "usage_metadata", None), duration_ms, text)
        return list(result.embeddings[0].values), usage

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

        client = genai.Client(api_key=self.api_key)
        t0 = time.monotonic()
        response = client.models.generate_content(model=self.model_name, contents=prompt)
        duration_ms = int((time.monotonic() - t0) * 1000)

        raw = response.text.strip()
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

        usage = _usage_from_metadata(self.model_name, getattr(response, "usage_metadata", None), duration_ms, prompt)

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

        client = genai.Client(api_key=self.api_key)
        contents = [
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt,
        ]

        t0 = time.monotonic()
        response = client.models.generate_content(model=self.model_name, contents=contents)
        duration_ms = int((time.monotonic() - t0) * 1000)

        import json, re
        raw = response.text.strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()

        usage = _usage_from_metadata(self.model_name, getattr(response, "usage_metadata", None), duration_ms, prompt)

        try:
            fields = json.loads(raw)
        except Exception:
            fields = {}

        return fields, usage

    def transcribe_audio_verbatim(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> tuple[str, "UsageData"]:
        """Transcreve o áudio fielmente, sem resumir. Retorna o texto e os dados de uso."""
        import time as _time

        prompt = """Transcreva exatamente o que foi dito no áudio, em português, sem resumir, sem interpretar, sem adicionar ou omitir nenhuma informação. Retorne apenas o texto transcrito, sem títulos, sem explicações adicionais."""

        client = genai.Client(api_key=self.api_key)
        contents = [
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            prompt,
        ]

        t0 = _time.monotonic()
        response = client.models.generate_content(model=self.model_name, contents=contents)
        duration_ms = int((_time.monotonic() - t0) * 1000)

        usage = _usage_from_metadata(self.model_name, getattr(response, "usage_metadata", None), duration_ms, prompt)

        return response.text.strip(), usage

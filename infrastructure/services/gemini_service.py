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

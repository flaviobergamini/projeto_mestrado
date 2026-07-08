import logging
import google.ai.generativelanguage_v1beta as glm
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIMENSIONS = 768


class GeminiService:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL or "gemini-2.0-flash"
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

    def generate_text(self, prompt: str, system_instruction: str | None = None) -> str:
        messages = []
        if system_instruction:
            messages.append(SystemMessage(content=system_instruction))
        messages.append(HumanMessage(content=prompt))
        response = self._llm.invoke(messages)
        return response.content

    def generate_embedding(self, text: str) -> list[float]:
        req = glm.EmbedContentRequest(
            model=self.embedding_model_name,
            content=glm.Content(parts=[glm.Part(text=text)]),
            output_dimensionality=EMBEDDING_DIMENSIONS,
        )
        resp = self._embed_client.embed_content(req)
        return list(resp.embedding.values)

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.generate_embedding(t) for t in texts]

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings  # Gemini
from core.config import settings
import asyncio

class LLMService:
    def __init__(self):
        pass

    def configure(self, provider: str):
        self.provider = provider

        if self.provider == "openai":
            self.llm = ChatOpenAI(model=settings.GPT_MODEL, api_key=settings.OPENAI_API_KEY)
            self.embedding_model = OpenAIEmbeddings(model=settings.GPT_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)

        elif self.provider == "groq":
            self.llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY)
            # para embeddings você pode usar HuggingFace local
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

        elif self.provider == "gemini":
            self.llm = ChatGoogleGenerativeAI(model=settings.GEMINI_MODEL, google_api_key=settings.GEMINI_API_KEY)
            self.embedding_model = GoogleGenerativeAIEmbeddings(model=settings.GEMINI_EMBEDDING_MODEL, google_api_key=settings.GEMINI_API_KEY)

        else:
            raise ValueError("Provider não suportado")

    async def chat(self, prompt: str) -> str:
        try:
            resp = self.llm.invoke(prompt)
            return resp.content
        except Exception as e:
            print(f"Erro ao chamar LLM: {e}")
            raise e

    async def generate_embeddings(self, text: str) -> list[float]:
        if self.provider == "groq":
            # HuggingFace já roda local
            return await asyncio.to_thread(self.embedding_model.encode, text)
        else:
            return self.embedding_model.embed_query(text)

    def split_text(self, text: str) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        return splitter.split_text(text)
    
    def getProvider(self) -> str:
        return self.provider

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    GPT_MODEL = os.getenv("GPT_MODEL")
    GPT_EMBEDDING_MODEL = os.getenv("GPT_EMBEDDING_MODEL")

settings = Settings()
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL")
    GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL")

    GPT_MODEL = os.getenv("GPT_MODEL")
    GPT_EMBEDDING_MODEL = os.getenv("GPT_EMBEDDING_MODEL")

    GROQ_MODEL = os.getenv("GROQ_MODEL")
    JWT_SECRET = os.getenv("JWT_SECRET")

    # Supabase Storage
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "agents-buket")

settings = Settings()
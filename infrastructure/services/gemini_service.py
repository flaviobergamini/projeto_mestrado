import google.generativeai as genai
from core.config import settings
from typing import Optional

class GeminiAgent:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-pro")

    def chat(self, prompt: str, context: Optional[str] = None):
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}" if context else prompt
        
        resposta = self.model.generate_content(full_prompt)
        return resposta.text

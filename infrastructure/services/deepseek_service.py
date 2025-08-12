from groq import Groq
from core.config import settings
from typing import Optional


class DeepseekService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def chat(self, prompt: str, context: Optional[str] = None):
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}" if context else prompt

        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": full_prompt}],
            model='deepseek-r1-distill-llama-70b',
            temperature=0.7,
            max_tokens=1024,
        )

        response = chat_completion.choices[0].message.content

        return response
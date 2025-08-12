from openai import OpenAI
from core.config import settings
from typing import Optional


class GptService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(self, prompt: str, context: Optional[str] = None):
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}" if context else prompt

        chat_completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        response = chat_completion.choices[0].message.content
        return response
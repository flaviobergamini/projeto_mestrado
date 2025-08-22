from openai import AsyncOpenAI
from core.config import settings
from typing import Optional


class GptService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(self, prompt: str, context: Optional[str] = None):
        full_prompt = f"Context: {context}\n\nQuestion: {prompt}" if context else prompt

        chat_completion = self.client.chat.completions.create(
            model=settings.GPT_MODEL,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )

        response = chat_completion.choices[0].message.content
        return response
    
    async def generate_embeddings(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(input=text, model=settings.GPT_EMBEDDING_MODEL)

        return response.data[0].embedding
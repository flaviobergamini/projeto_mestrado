from openai import OpenAI
from core.config import settings


class GptService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def chat(self, user_id: str, question: str):
        chat_completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente útil."},
                {"role": "user", "content": question}
            ]
        )

        response = chat_completion.choices[0].message.content
        return response
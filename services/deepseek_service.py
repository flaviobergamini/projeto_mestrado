from groq import Groq
from core.config import settings


class DeepseekService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def chat(self, user_id: str, question: str):
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            model='deepseek-r1-distill-llama-70b',
            temperature=0.7,
            max_tokens=1024,
        )

        response = chat_completion.choices[0].message.content

        return response
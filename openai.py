import os
from .base import LLMAdapter


class OpenAIAdapter(LLMAdapter):
    def __init__(self, model: str = "gpt-4o"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        except ImportError:
            raise ImportError("pip install openai")
        self.model = model

    @property
    def nome(self) -> str:
        return f"openai/{self.model}"

    def enviar(self, prompt: str, system: str = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resposta = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1500,
        )
        return resposta.choices[0].message.content

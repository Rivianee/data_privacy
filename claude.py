import os
import anthropic
from .base import LLMAdapter


class ClaudeAdapter(LLMAdapter):
    def __init__(self, model: str = "claude-opus-4-5"):
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

    @property
    def nome(self) -> str:
        return f"claude/{self.model}"

    def enviar(self, prompt: str, system: str = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system:
            kwargs["system"] = system
        resposta = self.client.messages.create(**kwargs)
        return resposta.content[0].text

import os
from .base import LLMAdapter


class GeminiAdapter(LLMAdapter):
    def __init__(self, model: str = "gemini-1.5-pro"):
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
            self.client = genai.GenerativeModel(model)
        except ImportError:
            raise ImportError("pip install google-generativeai")
        self.model = model

    @property
    def nome(self) -> str:
        return f"gemini/{self.model}"

    def enviar(self, prompt: str, system: str = None) -> str:
        texto = f"{system}\n\n{prompt}" if system else prompt
        resposta = self.client.generate_content(texto)
        return resposta.text

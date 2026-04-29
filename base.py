"""
Interface base para qualquer LLM.
Pra adicionar um novo: herda LLMAdapter e implementa `enviar`.
"""

from abc import ABC, abstractmethod


class LLMAdapter(ABC):
    @abstractmethod
    def enviar(self, prompt: str, system: str = None) -> str:
        """Envia prompt anonimizado, retorna resposta com tokens."""
        pass

    @property
    @abstractmethod
    def nome(self) -> str:
        pass

"""
PIIProxy — intercepta prompts, anonimiza, chama qualquer LLM, destokeniza.
O dado real nunca sai da sua infra.
"""

import sys
sys.path.insert(0, "/home/claude/pii_proxy")

from detector import detectar_pii
from tokenizer import PIITokenizer
from adapters.base import LLMAdapter

SYSTEM_HINT = (
    "Tokens in brackets like [NOME_PESSOA_XXXX] or [CPF_XXXX] are placeholders "
    "for real values. Treat them as real entities in your analysis. "
    "Use the same tokens in your response — never invent or modify them."
)


class PIIProxy:
    def __init__(self, adapter: LLMAdapter):
        """
        adapter: qualquer LLMAdapter — Claude, OpenAI, Gemini, etc.

        Exemplo:
            from adapters.claude import ClaudeAdapter
            proxy = PIIProxy(adapter=ClaudeAdapter())
        """
        self.adapter = adapter

    def enviar(self, prompt: str, system: str = None, verbose: bool = False) -> str:
        tokenizer = PIITokenizer()

        # 1. Detecta e anonimiza
        matches = detectar_pii(prompt)
        prompt_limpo = tokenizer.tokenizar(prompt, matches)

        # 2. Injeta hint no system prompt pra LLM entender os tokens
        system_final = SYSTEM_HINT
        if system:
            system_final = f"{system}\n\n{SYSTEM_HINT}"

        if verbose:
            self._log(prompt, prompt_limpo, tokenizer, system_final)

        # 3. Chama o LLM — qualquer um
        resposta_tokens = self.adapter.enviar(prompt_limpo, system=system_final)

        # 4. Destokeniza a resposta
        resposta_final = tokenizer.destokenizar(resposta_tokens)

        if verbose:
            print(f"\n📥 RESPOSTA DO LLM ({self.adapter.nome}) com tokens:")
            print(resposta_tokens)
            print("\n✅ RESPOSTA FINAL (destokenizada):")
            print(resposta_final)

        return resposta_final

    def _log(self, original: str, limpo: str, tok: PIITokenizer, system: str):
        print("\n" + "="*60)
        print(f"🤖 LLM: {self.adapter.nome}")
        print("\n📤 PROMPT ORIGINAL:")
        print(original)
        print("\n🔒 PROMPT ENVIADO AO LLM (anonimizado):")
        print(limpo)
        print("\n🗝️  MAPEAMENTO (fica só no seu servidor):")
        for token, valor in tok.resumo().items():
            print(f"   {token} → {valor}")
        print("="*60)

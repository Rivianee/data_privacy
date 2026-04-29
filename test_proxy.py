"""
Testes unitários com dados reais brasileiros.
Cobre: detector, tokenizer, bug segunda ocorrência, destokenização.
"""

import sys, re
sys.path.insert(0, "/home/claude/pii_proxy")

from detector import detectar_pii, PIIMatch
from tokenizer import PIITokenizer


# ─── helpers ────────────────────────────────────────────────────────────────

def tipos_detectados(texto: str) -> set:
    return {m.entity_type for m in detectar_pii(texto)}

def valores_detectados(texto: str) -> set:
    return {m.value for m in detectar_pii(texto)}

def tokenizar(texto: str) -> tuple[str, PIITokenizer]:
    tok = PIITokenizer()
    matches = detectar_pii(texto)
    resultado = tok.tokenizar(texto, matches)
    return resultado, tok

TOKEN_RE = re.compile(r"\[[A-Z_]+_[0-9A-F]{8}\]")


# ─── Detector: dados estruturados ───────────────────────────────────────────

def test_cpf_com_mascara():
    assert "CPF" in tipos_detectados("CPF: 347.829.104-57")

def test_cpf_sem_mascara():
    assert "CPF" in tipos_detectados("cpf 34782910457")

def test_cnpj():
    assert "CNPJ" in tipos_detectados("CNPJ: 45.231.887/0001-93")

def test_email():
    assert "EMAIL" in tipos_detectados("contato: joao.silva@empresa.com.br")

def test_email_subdominio():
    assert "EMAIL" in tipos_detectados("enviar para rh@grupo.construtora.com.br")

def test_valor_financeiro():
    assert "VALOR_FINANCEIRO" in tipos_detectados("salário de R$ 12.400,00 mensais")

def test_valor_financeiro_sem_espaco():
    assert "VALOR_FINANCEIRO" in tipos_detectados("bônus de R$8.200,00")

def test_telefone_com_ddd():
    assert "TELEFONE" in tipos_detectados("fone: (11) 98823-4471")

def test_telefone_fixo():
    # Telefone fixo precisa de DDD pra não gerar falsos positivos com ramais/protocolos
    assert "TELEFONE" in tipos_detectados("fone fixo (21) 3021-4400")

def test_rg():
    assert "RG" in tipos_detectados("RG: 28.374.591-4")

def test_ip():
    assert "IP" in tipos_detectados("acesso via 192.168.1.100")


# ─── Detector: nomes próprios ────────────────────────────────────────────────

def test_nome_completo():
    assert "NOME_PESSOA" in tipos_detectados("funcionário Marcos Antônio Ferreira da Silva foi")

def test_nome_dois_tokens():
    assert "NOME_PESSOA" in tipos_detectados("aprovado por Fernanda Santos")

def test_nome_com_preposicao():
    assert "NOME_PESSOA" in tipos_detectados("Patrícia Lima Cavalcante assinou")

def test_nome_nao_detecta_palavra_unica():
    assert "NOME_PESSOA" not in tipos_detectados("O Gerente aprovou")

def test_nome_nao_detecta_mes():
    assert "NOME_PESSOA" not in tipos_detectados("prazo até Dezembro deste ano")


# ─── Tokenizer: substituição correta ────────────────────────────────────────

def test_token_substitui_cpf():
    resultado, _ = tokenizar("CPF do funcionário: 347.829.104-57")
    assert "347.829.104-57" not in resultado
    assert TOKEN_RE.search(resultado)

def test_token_substitui_email():
    resultado, _ = tokenizar("enviar para joao@empresa.com")
    assert "joao@empresa.com" not in resultado

def test_token_substitui_valor():
    resultado, _ = tokenizar("salário R$ 15.000,00 aprovado")
    assert "R$ 15.000,00" not in resultado

def test_token_substitui_nome():
    resultado, _ = tokenizar("contrato com Roberto Carlos Mendonça assinado")
    assert "Roberto Carlos Mendonça" not in resultado

def test_mesmo_valor_mesmo_token():
    """Mesmo valor no texto deve virar o mesmo token (consistência)."""
    texto = "João Silva aprovou. Confirmado por João Silva."
    resultado, tok = tokenizar(texto)
    tokens = TOKEN_RE.findall(resultado)
    # Todos tokens de João Silva devem ser idênticos
    tokens_nome = [t for t in tokens if "NOME" in t]
    assert len(set(tokens_nome)) == 1, f"Tokens diferentes para mesmo nome: {tokens_nome}"


# ─── BUG FIX: segunda ocorrência ─────────────────────────────────────────────

def test_segunda_ocorrencia_nome():
    """Bug corrigido: nome que aparece 2x deve ser substituído nas 2 ocorrências."""
    texto = (
        "Marcos Antônio Ferreira da Silva foi contratado em 2018. "
        "O desempenho de Marcos Antônio Ferreira da Silva foi excelente."
    )
    resultado, _ = tokenizar(texto)
    assert resultado.count("Marcos Antônio Ferreira da Silva") == 0, \
        "Nome ainda aparece no texto após tokenização!"

def test_segunda_ocorrencia_cpf():
    """CPF repetido deve sumir nas duas ocorrências."""
    texto = "CPF 347.829.104-57 cadastrado. Pagamento para 347.829.104-57 liberado."
    resultado, _ = tokenizar(texto)
    assert "347.829.104-57" not in resultado

def test_segunda_ocorrencia_email():
    texto = "De: joao@emp.com. Para: joao@emp.com. Cópia: joao@emp.com."
    resultado, _ = tokenizar(texto)
    assert "joao@emp.com" not in resultado


# ─── Destokenização ──────────────────────────────────────────────────────────

def test_destokenizacao_restaura_nome():
    texto = "Relatório de Ana Paula Rodrigues aprovado."
    resultado, tok = tokenizar(texto)
    restaurado = tok.destokenizar(resultado)
    assert "Ana Paula Rodrigues" in restaurado

def test_destokenizacao_restaura_cpf():
    texto = "CPF: 598.341.072-18 verificado."
    resultado, tok = tokenizar(texto)
    restaurado = tok.destokenizar(resultado)
    assert "598.341.072-18" in restaurado

def test_destokenizacao_multiplos_valores():
    texto = "Marcos Ferreira, CPF 123.456.789-09, email marcos@emp.com, salário R$ 9.000,00"
    resultado, tok = tokenizar(texto)
    restaurado = tok.destokenizar(resultado)
    assert "123.456.789-09" in restaurado
    assert "marcos@emp.com" in restaurado
    assert "R$ 9.000,00" in restaurado

def test_destokenizacao_idempotente():
    """Destokenizar duas vezes não quebra nada."""
    texto = "Luciana Barros recebeu R$ 5.000,00"
    resultado, tok = tokenizar(texto)
    d1 = tok.destokenizar(resultado)
    d2 = tok.destokenizar(d1)
    assert d1 == d2


# ─── Caso integrado realista ─────────────────────────────────────────────────

def test_caso_rescisao_completo():
    """Simula o caso de RH com múltiplos tipos de PII."""
    texto = """
    Funcionário: Carlos Eduardo Lima Pereira
    CPF: 712.384.950-61
    Email: carlos.pereira@construtora.com.br
    Salário: R$ 18.750,00
    CNPJ da empresa: 33.456.789/0001-12
    Contato RH: (21) 3344-5566
    
    Carlos Eduardo Lima Pereira solicitou rescisão em 15/04/2025.
    Pagamento de R$ 18.750,00 a ser processado para o CPF 712.384.950-61.
    """
    resultado, tok = tokenizar(texto)

    # Nenhum dado sensível no texto enviado ao Claude
    assert "Carlos Eduardo Lima Pereira" not in resultado
    assert "712.384.950-61" not in resultado
    assert "carlos.pereira@construtora.com.br" not in resultado
    assert "R$ 18.750,00" not in resultado

    # Destokenização restaura tudo
    restaurado = tok.destokenizar(resultado)
    assert "Carlos Eduardo Lima Pereira" in restaurado
    assert "712.384.950-61" in restaurado


# ─── Adapter pattern ─────────────────────────────────────────────────────────

def test_adapter_interface():
    """Qualquer adapter deve implementar enviar() e nome."""
    from adapters.base import LLMAdapter
    import inspect
    assert inspect.isabstract(LLMAdapter)
    assert "enviar" in [m[0] for m in inspect.getmembers(LLMAdapter)]
    assert "nome" in [m[0] for m in inspect.getmembers(LLMAdapter)]

def test_proxy_agnostico_com_mock():
    """PIIProxy funciona com qualquer adapter — testa com mock."""
    import sys
    sys.path.insert(0, "/home/claude/pii_proxy")
    from proxy import PIIProxy
    from adapters.base import LLMAdapter

    class MockLLM(LLMAdapter):
        """Simula LLM: devolve os tokens intactos."""
        @property
        def nome(self): return "mock/test"
        def enviar(self, prompt, system=None): return f"Análise: {prompt}"

    proxy = PIIProxy(adapter=MockLLM())
    texto = "Funcionário João Pedro Alves, CPF 111.222.333-44, salário R$ 5.000,00"
    resposta = proxy.enviar(texto)

    # Dado real restaurado na resposta final
    assert "João Pedro Alves" in resposta
    assert "111.222.333-44" in resposta
    assert "R$ 5.000,00" in resposta

def test_proxy_mock_nunca_ve_dado_real():
    """O LLM nunca recebe dado real — só tokens."""
    import sys
    sys.path.insert(0, "/home/claude/pii_proxy")
    from proxy import PIIProxy
    from adapters.base import LLMAdapter

    prompts_recebidos = []

    class MockLLM(LLMAdapter):
        @property
        def nome(self): return "mock/spy"
        def enviar(self, prompt, system=None):
            prompts_recebidos.append(prompt)
            return prompt  # devolve igual

    proxy = PIIProxy(adapter=MockLLM())
    proxy.enviar("Contrato com Ana Beatriz Lima, CNPJ 12.345.678/0001-99")

    assert len(prompts_recebidos) == 1
    prompt_enviado = prompts_recebidos[0]
    assert "Ana Beatriz Lima" not in prompt_enviado
    assert "12.345.678/0001-99" not in prompt_enviado

def test_troca_adapter_mesmo_resultado():
    """Dois adapters mock diferentes, mesma anonimização."""
    import sys
    sys.path.insert(0, "/home/claude/pii_proxy")
    from proxy import PIIProxy
    from adapters.base import LLMAdapter

    class MockA(LLMAdapter):
        @property
        def nome(self): return "mock/a"
        def enviar(self, prompt, system=None): return prompt

    class MockB(LLMAdapter):
        @property
        def nome(self): return "mock/b"
        def enviar(self, prompt, system=None): return prompt

    texto = "Email: ceo@empresa.com, CPF: 999.888.777-66"

    r1 = PIIProxy(adapter=MockA()).enviar(texto)
    r2 = PIIProxy(adapter=MockB()).enviar(texto)

    # Ambos restauram os mesmos dados reais
    assert "ceo@empresa.com" in r1 and "ceo@empresa.com" in r2
    assert "999.888.777-66" in r1 and "999.888.777-66" in r2


# ─── Runner ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback

    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passou = 0
    falhou = 0

    for fn in testes:
        try:
            fn()
            print(f"  ✅ {fn.__name__}")
            passou += 1
        except Exception as e:
            print(f"  ❌ {fn.__name__}")
            traceback.print_exc()
            falhou += 1

    print(f"\n{'='*50}")
    print(f"  {passou} passaram  |  {falhou} falharam  |  {passou+falhou} total")
    print(f"{'='*50}")
    sys.exit(1 if falhou else 0)

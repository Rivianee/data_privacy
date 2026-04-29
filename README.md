# 🔒 claude-pii-proxy

**Open source middleware that anonymizes sensitive data before sending it to Claude — and restores it in the response.**

Your data never leaves your infrastructure. Claude only sees tokens.

---

## The Problem

Companies want to use Claude for legal analysis, HR decisions, financial reports — but can't risk sending real names, CPFs, CNPJs, salaries, and emails to an external API.

Moving to another provider doesn't solve it. The data still leaves.

## The Solution

```
User prompt (with real data)
        ↓
[Classifier] → detects sensitive fields
        ↓
[Anonymizer] → replaces with opaque tokens
        ↓
Claude receives clean prompt  ← only this crosses the network
        ↓
[De-anonymizer] → restores real data in response
        ↓
User sees normal response
```

The token-to-value mapping lives **only in your server's memory**. Claude never sees it.

---

## What Gets Detected

| Type | Example |
|---|---|
| CPF | `347.829.104-57` |
| CNPJ | `45.231.887/0001-93` |
| Email | `joao@empresa.com.br` |
| Full name | `Marcos Antônio Ferreira da Silva` |
| Financial value | `R$ 12.400,00` |
| Phone (with DDD) | `(11) 98823-4471` |
| RG | `28.374.591-4` |
| IP address | `192.168.1.100` |
| CEP | `01310-100` |

---

## Quick Start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # or OPENAI_API_KEY / GEMINI_API_KEY
```

```python
from proxy import PIIProxy
from adapters.claude import ClaudeAdapter
# from adapters.openai import OpenAIAdapter
# from adapters.gemini import GeminiAdapter

# swap the adapter — everything else stays the same
proxy = PIIProxy(adapter=ClaudeAdapter())

resposta = proxy.enviar("""
    Analyze the termination case of Marcos Antônio Ferreira da Silva,
    CPF 347.829.104-57, salary R$ 12.400,00.
    He shared confidential reports with roberto@competitor.com.
    Is there grounds for termination for cause?
""")

print(resposta)
# Response contains real names/values — restored transparently
```

---

## How It Works Internally

**What Claude receives:**
```
Analyze the termination case of [NOME_PESSOA_BA81A47F],
CPF [CPF_04963FB8], salary [VALOR_FINANCEIRO_DBEF2D05].
He shared confidential reports with [EMAIL_429CC847].
Is there grounds for termination for cause?
```

**Mapping stored only in your server:**
```
[NOME_PESSOA_BA81A47F] → Marcos Antônio Ferreira da Silva
[CPF_04963FB8]         → 347.829.104-57
[VALOR_FINANCEIRO_DBEF2D05] → R$ 12.400,00
[EMAIL_429CC847]       → roberto@competitor.com
```

---

## Run with verbose (see everything)

```python
proxy.enviar(prompt, verbose=True)
```

Output:
```
📤 ORIGINAL PROMPT: ...
🔒 PROMPT SENT TO CLAUDE: ...
🗝️  MAPPING (stays on your server): ...
📥 CLAUDE RESPONSE (with tokens): ...
✅ FINAL RESPONSE (restored): ...
```

---

## Run Tests

```bash
python test_proxy.py
```

```
✅ test_cpf_com_mascara
✅ test_cnpj
✅ test_email
✅ test_nome_completo
✅ test_segunda_ocorrencia_nome       ← repeated values always replaced
✅ test_proxy_mock_nunca_ve_dado_real ← LLM never sees real data
✅ test_troca_adapter_mesmo_resultado ← swap LLM, same anonymization
✅ test_caso_rescisao_completo
...
33 passed | 0 failed
```

---

## Architecture

```
pii_proxy/
├── detector.py          # regex-based PII classifier (no NLP model needed)
├── tokenizer.py         # token vault — maps real values ↔ tokens
├── proxy.py             # LLM-agnostic interceptor
├── adapters/
│   ├── base.py          # LLMAdapter interface
│   ├── claude.py        # Anthropic Claude
│   ├── openai.py        # OpenAI GPT-4 / GPT-4o
│   └── gemini.py        # Google Gemini
├── exemplo_rh.py        # realistic HR example
└── test_proxy.py        # 33 unit tests with real Brazilian data
```

**Adding a new LLM takes ~10 lines** — inherit `LLMAdapter`, implement `enviar()` and `nome`.

---

## Security Model

- Token mapping is held **in memory only** — never written to disk or logs
- Claude receives a prompt with no PII — even if Anthropic logs requests, your data is safe
- You can run this on-premise, in your own VPC, or in an air-gapped environment
- Audit trail: call `tokenizer.resumo()` to log the mapping on your own infrastructure

---

## Roadmap

- [ ] Context hint in system prompt (tell Claude tokens are placeholders)
- [ ] Per-department policies (block, mask, or warn by entity type)
- [ ] Audit dashboard
- [ ] LGPD / GDPR compliance report
- [ ] Support for additional languages and entity types
- [ ] CLI interface

---

## Contributing

PRs welcome. If you add a new entity type, add a test in `test_proxy.py` with a real example.

---

## License

MIT — use it, fork it, sell it, install it on-premise. Do whatever you need.

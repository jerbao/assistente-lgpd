# Assistente LGPD

Assistente que tira dúvidas sobre a Lei Geral de Proteção de Dados (LGPD).

## Como rodar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Preencha a `OPENROUTER_API_KEY` no `.env` e monte a base:

```bash
python preparar.py
python indexar.py
```

O servidor MCP roda sozinho com:

```bash
python servidor.py
```

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

Abra a interface:

```bash
streamlit run app.py
```

A interface inicia sozinha o servidor MCP do projeto (`servidor.py`) e o `mcp-server-time`. Para testar o servidor sem a interface:

```bash
python servidor.py
```

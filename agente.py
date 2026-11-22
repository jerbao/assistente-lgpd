import sys
from pathlib import Path
from typing import Annotated

from langchain.chat_models import init_chat_model
from langchain.mcp import MCPAdapter
from langchain_core.messages import AnyMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from typing_extensions import TypedDict

from indexar import PASTA_PROJETO

MODELO = "openrouter:google/gemma-4-26b-a4b-it"

SISTEMA = """# Papel
Você tira dúvidas sobre a LGPD e as resoluções da ANPD para o setor de privacidade de empresas pequenas.

# Regras
- Para qualquer pergunta sobre a lei, consulte a base com buscarNaBase antes de responder. Nunca responda de memória.
- Se o trecho vier cortado, leia o artigo inteiro com lerArtigo.
- Para multa máxima e prazos, use as ferramentas de cálculo.
- Termine a resposta citando o documento e o artigo, como (LGPD, art. 19).
- Seja breve: no máximo cinco frases."""


class Estado(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def criarAdaptador() -> MCPAdapter:
    return MCPAdapter({"mcpServers": {
        "lgpd": {"command": sys.executable, "args": [str(PASTA_PROJETO / "servidor.py")]},
    }})


async def montarGrafo(adaptador: MCPAdapter):
    ferramentas = await adaptador.list_tools()
    modelo = init_chat_model(MODELO, temperature=0.0).bind_tools(ferramentas)

    async def agente(estado: Estado) -> dict:
        resposta = await modelo.ainvoke([SystemMessage(SISTEMA), *estado["messages"]])
        return {"messages": [resposta]}

    grafo = StateGraph(Estado)
    grafo.add_node("agente", agente)
    grafo.add_node("ferramentas", ToolNode(ferramentas))
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition, {"tools": "ferramentas", END: END})
    grafo.add_edge("ferramentas", "agente")
    return grafo.compile()


if __name__ == "__main__":
    import asyncio

    async def perguntar(pergunta: str) -> None:
        adaptador = criarAdaptador()
        async with adaptador:
            grafo = await montarGrafo(adaptador)
            resultado = await grafo.ainvoke({"messages": [("user", pergunta)]})
        for mensagem in resultado["messages"]:
            for chamada in getattr(mensagem, "tool_calls", []):
                print("->", chamada["name"], chamada["args"])
        print(resultado["messages"][-1].text)

    asyncio.run(perguntar(" ".join(sys.argv[1:]) or "Qual o prazo para comunicar um incidente de segurança à ANPD?"))

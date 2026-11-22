import sys
from pathlib import Path
from typing import Annotated, Literal

from langchain.chat_models import init_chat_model
from langchain.mcp import MCPAdapter
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from pydantic import BaseModel, Field
from typing_extensions import NotRequired, TypedDict

from indexar import PASTA_PROJETO

MODELO = "openrouter:google/gemma-4-26b-a4b-it"

SISTEMA = """# Papel
Você tira dúvidas sobre a LGPD e as resoluções da ANPD para o setor de privacidade de empresas pequenas.

# Regras
- Para qualquer pergunta sobre a lei, consulte a base com buscarNaBase antes de responder. Nunca responda de memória.
- Se o trecho vier cortado, leia o artigo inteiro com lerArtigo.
- Para multa máxima e prazos, use as ferramentas de cálculo.
- Quando o usuário disser "hoje", "ontem" ou não disser a data, consulte a data atual com tempo_get_current_time no fuso America/Sao_Paulo. Nunca suponha a data.
- Só use pequenoPorte=true se o usuário disser que a empresa é microempresa, empresa de pequeno porte ou startup.
- Termine a resposta citando o documento e o artigo, como (LGPD, art. 19).
- Seja breve: no máximo cinco frases."""

AVALIACAO = """# Tarefa
Diga se algum dos trechos abaixo traz a informação que a pergunta pede, mesmo com outras palavras.
Responda que não quando os trechos só falam do mesmo tema sem responder a pergunta.

# Pergunta
{pergunta}

# Trechos
{trechos}"""

SEM_RESPOSTA = "Os trechos recuperados não respondem à pergunta. Se um deles for um pedaço cortado do artigo certo, leia o artigo inteiro com lerArtigo. Se nenhum for, diga que não encontrou essa informação na LGPD nem nas resoluções da ANPD, sem citar artigo."


class Avaliacao(BaseModel):
    respondem: bool = Field(description="se algum trecho traz a informação que a pergunta pede")


class Estado(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    trechosRespondem: NotRequired[bool | None]


def ultimaPergunta(estado: Estado) -> str:
    return next(mensagem.text for mensagem in reversed(estado["messages"]) if isinstance(mensagem, HumanMessage))


def resultadosDaBusca(estado: Estado) -> list[str]:
    resultados = []
    for mensagem in reversed(estado["messages"]):
        if not isinstance(mensagem, ToolMessage):
            break
        if mensagem.name == "lgpd_buscarNaBase":
            resultados.append(mensagem.text)
    return resultados


def criarAdaptador() -> MCPAdapter:
    return MCPAdapter({"mcpServers": {
        "lgpd": {"command": sys.executable, "args": [str(PASTA_PROJETO / "servidor.py")]},
        "tempo": {"command": sys.executable, "args": ["-m", "mcp_server_time", "--local-timezone", "America/Sao_Paulo"]},
    }})


async def montarGrafo(adaptador: MCPAdapter):
    ferramentas = await adaptador.list_tools()
    modeloBase = init_chat_model(MODELO, temperature=0.0)
    modelo = modeloBase.bind_tools(ferramentas)
    avaliador = modeloBase.with_structured_output(Avaliacao)

    async def agente(estado: Estado) -> dict:
        instrucoes = [SystemMessage(SISTEMA)]
        if estado.get("trechosRespondem") is False:
            instrucoes.append(SystemMessage(SEM_RESPOSTA))
        resposta = await modelo.ainvoke([*instrucoes, *estado["messages"]])
        return {"messages": [resposta], "trechosRespondem": None}

    async def avaliarTrechos(estado: Estado) -> dict:
        avaliacao = await avaliador.ainvoke(AVALIACAO.format(pergunta=ultimaPergunta(estado), trechos="\n\n".join(resultadosDaBusca(estado))))
        return {"trechosRespondem": avaliacao.respondem}

    def depoisDasFerramentas(estado: Estado) -> Literal["avaliarTrechos", "agente"]:
        return "avaliarTrechos" if resultadosDaBusca(estado) else "agente"

    grafo = StateGraph(Estado)
    grafo.add_node("agente", agente)
    grafo.add_node("ferramentas", ToolNode(ferramentas))
    grafo.add_node("avaliarTrechos", avaliarTrechos)
    grafo.add_edge(START, "agente")
    grafo.add_conditional_edges("agente", tools_condition, {"tools": "ferramentas", END: END})
    grafo.add_conditional_edges("ferramentas", depoisDasFerramentas)
    grafo.add_edge("avaliarTrechos", "agente")
    return grafo.compile()


if __name__ == "__main__":
    import asyncio

    async def perguntar(pergunta: str) -> None:
        adaptador = criarAdaptador()
        async with adaptador:
            grafo = await montarGrafo(adaptador)
            ultima = None
            async for passo in grafo.astream({"messages": [("user", pergunta)]}, stream_mode="updates"):
                for no, atualizacao in passo.items():
                    for mensagem in atualizacao.get("messages", []):
                        ultima = mensagem
                        for chamada in getattr(mensagem, "tool_calls", []):
                            print("->", chamada["name"], chamada["args"])
                    if no == "avaliarTrechos":
                        print("-> avaliarTrechos: os trechos respondem?", atualizacao["trechosRespondem"])
        print(ultima.text)

    asyncio.run(perguntar(" ".join(sys.argv[1:]) or "Qual o prazo para comunicar um incidente de segurança à ANPD?"))

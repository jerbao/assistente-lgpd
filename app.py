import asyncio
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import ARQUIVO_MEMORIA, criarAdaptador, montarGrafo


def passosDoTurno(mensagens: list) -> tuple[list[str], list[str]]:
    ferramentas, skills = [], []
    for mensagem in mensagens:
        for chamada in getattr(mensagem, "tool_calls", []):
            if chamada["name"] == "carregarSkill":
                skills.append(chamada["args"]["nome"])
            else:
                argumentos = ", ".join(f"{chave}={valor!r}" for chave, valor in chamada["args"].items())
                ferramentas.append(f"{chamada['name']}({argumentos})")
    return ferramentas, skills


async def responder(pergunta: str, conversa: str) -> dict:
    adaptador = criarAdaptador()
    async with adaptador, AsyncSqliteSaver.from_conn_string(str(ARQUIVO_MEMORIA)) as memoria:
        grafo = await montarGrafo(adaptador, memoria)
        resultado = await grafo.ainvoke({"messages": [("user", pergunta)]}, {"configurable": {"thread_id": conversa}})
    mensagens = resultado["messages"]
    inicio = max(i for i, mensagem in enumerate(mensagens) if isinstance(mensagem, HumanMessage))
    ferramentas, skills = passosDoTurno(mensagens[inicio:])
    return {"texto": mensagens[-1].text, "ferramentas": ferramentas, "skills": skills}


def mostrarResposta(resposta: dict) -> None:
    st.markdown(resposta["texto"])
    if resposta["skills"]:
        st.caption("Skills carregadas: " + ", ".join(f"`{skill}`" for skill in resposta["skills"]))
    if resposta["ferramentas"]:
        with st.expander(f"Ferramentas chamadas ({len(resposta['ferramentas'])})"):
            for ferramenta in resposta["ferramentas"]:
                st.code(ferramenta, language=None)


st.set_page_config(page_title="Assistente LGPD", page_icon="🔒")
st.title("Assistente LGPD")
st.caption("Dúvidas sobre a LGPD e as resoluções da ANPD de comunicação de incidente e de agentes de pequeno porte.")

if "conversa" not in st.session_state:
    st.session_state.conversa = str(uuid.uuid4())
    st.session_state.historico = []

with st.sidebar:
    if st.button("Nova conversa", use_container_width=True):
        st.session_state.conversa = str(uuid.uuid4())
        st.session_state.historico = []
    st.caption(f"Conversa {st.session_state.conversa[:8]}")

for papel, conteudo in st.session_state.historico:
    with st.chat_message(papel):
        if papel == "user":
            st.markdown(conteudo)
        else:
            mostrarResposta(conteudo)

if pergunta := st.chat_input("Pergunte sobre a LGPD"):
    st.session_state.historico.append(("user", pergunta))
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Consultando a LGPD..."):
            resposta = asyncio.run(responder(pergunta, st.session_state.conversa))
        mostrarResposta(resposta)
    st.session_state.historico.append(("assistant", resposta))

import asyncio
import uuid

import streamlit as st
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agente import ARQUIVO_MEMORIA, criarAdaptador, montarGrafo


async def responder(pergunta: str, conversa: str) -> str:
    adaptador = criarAdaptador()
    async with adaptador, AsyncSqliteSaver.from_conn_string(str(ARQUIVO_MEMORIA)) as memoria:
        grafo = await montarGrafo(adaptador, memoria)
        resultado = await grafo.ainvoke({"messages": [("user", pergunta)]}, {"configurable": {"thread_id": conversa}})
    return resultado["messages"][-1].text


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

for papel, texto in st.session_state.historico:
    with st.chat_message(papel):
        st.markdown(texto)

if pergunta := st.chat_input("Pergunte sobre a LGPD"):
    st.session_state.historico.append(("user", pergunta))
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Consultando a LGPD..."):
            resposta = asyncio.run(responder(pergunta, st.session_state.conversa))
        st.markdown(resposta)
    st.session_state.historico.append(("assistant", resposta))

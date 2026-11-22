import asyncio

import streamlit as st

from agente import criarAdaptador, montarGrafo


async def responder(pergunta: str) -> str:
    adaptador = criarAdaptador()
    async with adaptador:
        grafo = await montarGrafo(adaptador)
        resultado = await grafo.ainvoke({"messages": [("user", pergunta)]})
    return resultado["messages"][-1].text


st.set_page_config(page_title="Assistente LGPD", page_icon="🔒")
st.title("Assistente LGPD")
st.caption("Dúvidas sobre a LGPD e as resoluções da ANPD de comunicação de incidente e de agentes de pequeno porte.")

if "historico" not in st.session_state:
    st.session_state.historico = []

for papel, texto in st.session_state.historico:
    with st.chat_message(papel):
        st.markdown(texto)

if pergunta := st.chat_input("Pergunte sobre a LGPD"):
    st.session_state.historico.append(("user", pergunta))
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Consultando a LGPD..."):
            resposta = asyncio.run(responder(pergunta))
        st.markdown(resposta)
    st.session_state.historico.append(("assistant", resposta))

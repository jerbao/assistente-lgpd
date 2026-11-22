import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.embeddings import init_embeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

PASTA_DADOS = Path("dados")
PASTA_INDICE = PASTA_DADOS / "chroma"


def criarEmbeddings():
    return init_embeddings(
        "openai:openai/text-embedding-3-small",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        check_embedding_ctx_length=False,
    )


def abrirIndice() -> Chroma:
    return Chroma(
        collection_name="lgpd",
        embedding_function=criarEmbeddings(),
        persist_directory=str(PASTA_INDICE),
        collection_metadata={"hnsw:space": "cosine"},
    )


def dividirArtigos(base: dict) -> list[Document]:
    divisor = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200, separators=[" § ", " Parágrafo único", "; ", " "])
    trechos = []
    for chave, documento in base.items():
        for numero, texto in documento["artigos"].items():
            for posicao, pedaco in enumerate(divisor.split_text(texto)):
                trechos.append(Document(
                    id=f"{chave}-art{numero}-{posicao}",
                    page_content=f"[{documento['nome']}, art. {numero}] {pedaco}",
                    metadata={"documento": documento["nome"], "artigo": numero, "fonte": documento["url"]},
                ))
    return trechos


if __name__ == "__main__":
    base = json.loads((PASTA_DADOS / "artigos.json").read_text())
    trechos = dividirArtigos(base)
    indice = abrirIndice()
    indice.add_documents(trechos, ids=[trecho.id for trecho in trechos])
    print(len(trechos), "trechos indexados, total no índice:", len(indice.get()["ids"]))

from fastmcp import FastMCP

from indexar import abrirIndice

mcp = FastMCP("lgpd")


@mcp.tool(description=(
    "Busca trechos da LGPD e das resoluções da ANPD (comunicação de incidente e agentes de pequeno porte). "
    "Devolve cada trecho com o documento e o número do artigo. Escreva a consulta com os termos da lei, "
    "como \"titular\" e \"controlador\" em vez de \"cliente\" e \"empresa\". k é o número de trechos, de 1 a 10."
))
def buscarNaBase(consulta: str, k: int = 4) -> str:
    if not 1 <= k <= 10:
        return "erro: k deve estar entre 1 e 10"
    trechos = abrirIndice().similarity_search(consulta, k=k)
    return "\n\n".join(trecho.page_content for trecho in trechos)


if __name__ == "__main__":
    mcp.run(show_banner=False)

import json
import re
from datetime import date, timedelta

from fastmcp import FastMCP

from indexar import PASTA_DADOS, abrirIndice

mcp = FastMCP("lgpd")

DOCUMENTOS = {"lgpd": "LGPD", "incidente": "Resolução CD/ANPD nº 15/2024", "pequenoPorte": "Resolução CD/ANPD nº 2/2022"}
MULTA_PERCENTUAL = 0.02
MULTA_TETO = 50_000_000.00
PRAZOS = {
    "acessoTitular": (15, "corridos", "LGPD, art. 19, II"),
    "incidenteAnpd": (3, "úteis", "Resolução CD/ANPD nº 15/2024, art. 6º"),
    "incidenteTitular": (3, "úteis", "Resolução CD/ANPD nº 15/2024, art. 9º"),
}


def somarDiasUteis(inicio: date, dias: int) -> date:
    atual = inicio
    while dias:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            dias -= 1
    return atual


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


@mcp.tool(description=(
    "Devolve o texto completo de um artigo, com todos os incisos e parágrafos. Use depois de uma busca, "
    "quando um trecho cortado não basta. documento é \"lgpd\", \"incidente\" (Resolução CD/ANPD nº 15/2024) "
    "ou \"pequenoPorte\" (Resolução CD/ANPD nº 2/2022); numero é como \"19\", \"art. 52\" ou \"55-J\"."
))
def lerArtigo(documento: str, numero: str) -> str:
    if documento not in DOCUMENTOS:
        return f"erro: documento deve ser um de {list(DOCUMENTOS)}"
    artigos = json.loads((PASTA_DADOS / "artigos.json").read_text())[documento]["artigos"]
    chave = re.sub(r"(?i)^art(igo)?\.?\s*|[º°\s]", "", numero.strip()).upper()
    if chave not in artigos:
        return f"erro: {DOCUMENTOS[documento]} não tem art. {numero}; os artigos vão do {next(iter(artigos))} ao {list(artigos)[-1]}"
    return artigos[chave]


@mcp.tool(description=(
    "Calcula o teto da multa simples da LGPD (art. 52, II): 2% do faturamento da empresa no Brasil no último "
    "exercício, sem os tributos, limitado a R$ 50 milhões por infração. faturamentoAnual em reais. É o máximo "
    "legal, não o valor que a ANPD aplicaria, que depende dos critérios do art. 52, § 1º."
))
def calcularMultaMaxima(faturamentoAnual: float) -> dict:
    if faturamentoAnual < 0:
        return {"erro": "o faturamento não pode ser negativo"}
    multa = min(faturamentoAnual * MULTA_PERCENTUAL, MULTA_TETO)
    return {"multaMaxima": round(multa, 2), "limitadaPeloTeto": multa == MULTA_TETO, "fundamento": "LGPD, art. 52, II"}


@mcp.tool(description=(
    "Calcula a data-limite de um prazo da LGPD. tipo é \"acessoTitular\" (declaração completa ao titular, "
    "15 dias corridos), \"incidenteAnpd\" ou \"incidenteTitular\" (comunicação de incidente, 3 dias úteis contados "
    "de quando o controlador soube que o incidente afetou dados pessoais). dataInicio no formato AAAA-MM-DD. "
    "pequenoPorte=true dobra o prazo para microempresas, empresas de pequeno porte e startups (Resolução CD/ANPD "
    "nº 2/2022, art. 14), exceto se fizerem tratamento de alto risco. Dias úteis pulam sábados e domingos, mas "
    "não feriados."
))
def calcularPrazo(tipo: str, dataInicio: str, pequenoPorte: bool = False) -> dict:
    if tipo not in PRAZOS:
        return {"erro": f"tipo deve ser um de {list(PRAZOS)}"}
    try:
        inicio = date.fromisoformat(dataInicio)
    except ValueError:
        return {"erro": f"data inválida: {dataInicio!r}; use o formato AAAA-MM-DD"}
    dias, contagem, fundamento = PRAZOS[tipo]
    if pequenoPorte:
        dias *= 2
        fundamento += " e Resolução CD/ANPD nº 2/2022, art. 14"
    limite = somarDiasUteis(inicio, dias) if contagem == "úteis" else inicio + timedelta(days=dias)
    return {"dataLimite": limite.isoformat(), "prazo": f"{dias} dias {contagem}", "fundamento": fundamento}


if __name__ == "__main__":
    mcp.run(show_banner=False)

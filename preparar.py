import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

PASTA_DADOS = Path(__file__).resolve().parent / "dados"
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

DOCUMENTOS = {
    "lgpd": {
        "nome": "LGPD",
        "url": "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm",
        "codificacao": "cp1252",
        "seletor": "body",
        "soAnexo": False,
    },
    "incidente": {
        "nome": "Resolução CD/ANPD nº 15/2024",
        "url": "https://www.in.gov.br/en/web/dou/-/resolucao-cd/anpd-n-15-de-24-de-abril-de-2024-556243024",
        "codificacao": "utf-8",
        "seletor": "div.texto-dou",
        "soAnexo": True,
    },
    "pequenoPorte": {
        "nome": "Resolução CD/ANPD nº 2/2022",
        "url": "https://www.gov.br/anpd/pt-br/acesso-a-informacao/institucional/atos-normativos/regulamentacoes_anpd/resolucao-cd-anpd-no-2-de-27-de-janeiro-de-2022",
        "codificacao": "utf-8",
        "seletor": "#page-document",
        "soAnexo": True,
    },
}


def baixar(url: str, destino: Path) -> Path:
    if not destino.exists():
        resposta = requests.get(url, headers={"User-Agent": NAVEGADOR}, timeout=60)
        resposta.raise_for_status()
        destino.write_bytes(resposta.content)
    return destino


def limparArtigo(texto: str) -> str:
    texto = re.sub(r"\(Revogad[oa]s? pel[oa][^)]*\)", "(Revogado)", texto)
    texto = re.sub(r"\((Incluíd|Redação dada|Vide|Promulgação|Produção de efeito)[^)]*\)\s*(Vigência)?", "", texto)
    texto = re.sub(r"\(Vigência\)", "", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.split(" Brasília")[0].strip()


def separarArtigos(arquivoHtml: Path, documento: dict) -> dict[str, str]:
    pagina = BeautifulSoup(arquivoHtml.read_bytes().decode(documento["codificacao"]), "html.parser")
    conteudo = pagina.select_one(documento["seletor"])
    for revogado in conteudo.find_all(["del", "strike", "s"]):
        revogado.decompose()
    texto = conteudo.get_text("\n")
    if documento["soAnexo"]:
        texto = texto[texto.index("ANEXO"):]
    inicios = list(re.finditer(r"(?m)^\s*Art\.\s?(\d+)\s?[º°o]?\s?(-\s?[A-Z])?[\s.]", texto))
    artigos = {}
    for atual, proximo in zip(inicios, inicios[1:] + [None]):
        numero = atual.group(1) + (atual.group(2) or "").replace(" ", "")
        corpo = texto[atual.start(): proximo.start() if proximo else len(texto)]
        artigos.setdefault(numero, limparArtigo(corpo))
    return artigos


if __name__ == "__main__":
    PASTA_DADOS.mkdir(exist_ok=True)
    base = {}
    for chave, documento in DOCUMENTOS.items():
        artigos = separarArtigos(baixar(documento["url"], PASTA_DADOS / f"{chave}.htm"), documento)
        base[chave] = {"nome": documento["nome"], "url": documento["url"], "artigos": artigos}
        print(documento["nome"], len(artigos), "artigos, do", next(iter(artigos)), "ao", list(artigos)[-1])
    (PASTA_DADOS / "artigos.json").write_text(json.dumps(base, ensure_ascii=False, indent=1))

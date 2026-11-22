import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL_LGPD = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709compilado.htm"
PASTA_DADOS = Path("dados")
NAVEGADOR = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def baixar(url: str, destino: Path) -> Path:
    if not destino.exists():
        resposta = requests.get(url, headers={"User-Agent": NAVEGADOR}, timeout=60)
        resposta.raise_for_status()
        destino.write_bytes(resposta.content)
    return destino


def separarArtigos(arquivoHtml: Path) -> dict[str, str]:
    pagina = BeautifulSoup(arquivoHtml.read_bytes().decode("cp1252"), "html.parser")
    texto = pagina.get_text("\n")
    inicios = list(re.finditer(r"(?m)^\s*Art\.\s?(\d+)\s?[º°o]?\s?(-\s?[A-Z])?[\s.]", texto))
    artigos = {}
    for atual, proximo in zip(inicios, inicios[1:] + [None]):
        numero = atual.group(1) + (atual.group(2) or "").replace(" ", "")
        corpo = texto[atual.start(): proximo.start() if proximo else len(texto)]
        artigos.setdefault(numero, re.sub(r"\s+", " ", corpo).strip())
    return artigos


if __name__ == "__main__":
    PASTA_DADOS.mkdir(exist_ok=True)
    artigos = separarArtigos(baixar(URL_LGPD, PASTA_DADOS / "lgpd.htm"))
    (PASTA_DADOS / "artigos.json").write_text(json.dumps(artigos, ensure_ascii=False, indent=1))
    print(len(artigos), "artigos, do", next(iter(artigos)), "ao", list(artigos)[-1])

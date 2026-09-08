"""
sincronizar_tabelas.py

Importa tabelas OFICIAIS da Reforma Tributária a partir de um arquivo CSV
baixado manualmente e converte para o formato usado pelo sistema.

Tabelas suportadas (--tipo):
  cclasstrib  -> gera data/cclasstrib_oficial.csv
  nbs         -> gera data/nbs_oficial.csv
  cindop      -> gera data/cindop_oficial.csv
  ctribnac    -> gera data/ctribnac_oficial.csv

cTribMun NÃO é importado por este script porque não existe uma tabela
nacional única — cada município publica a sua. Para isso, baixe a
planilha do seu município (ou do município do cliente) e salve
diretamente em data/ctribmun/<nome-do-municipio>.csv seguindo o layout
do arquivo data/ctribmun/_modelo_paulista_pe.csv.

Por que este script não baixa a tabela sozinho por padrão
-----------------------------------------------------------
O acesso via API/JSON aos portais oficiais normalmente exige certificado
digital, e o layout do arquivo pode mudar a cada versão do Informe/Nota
Técnica. Por segurança e para não gerar dados incorretos, o fluxo é:

  1. Baixar manualmente o arquivo oficial vigente:
       - cClassTrib/CST: Portal Nacional da NF-e > Documentos > Diversos
         ou https://dfe-portal.svrs.rs.gov.br/DFE/TabelaClassificacaoTributaria
       - NBS, cIndOp, cTribNac: Portal Nacional da NFS-e > Documentação
         Técnica: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica
     Se vier em .xlsx, exporte/converta para .csv antes.
     Salve em: data/oficial_bruto/<nome-do-arquivo>.csv

  2. Rodar, por exemplo:
       python src/sincronizar_tabelas.py --tipo cclasstrib \
           --arquivo data/oficial_bruto/tabela_cclasstrib.csv \
           --versao-it "2025.002 v1.60"

  3. Conferir o resultado no arquivo *_oficial.csv gerado e revisar o
     CHANGELOG.md (o script grava automaticamente).

Quando rodar isso
------------------
- Sempre que sair um novo Informe/Nota Técnica alterando qualquer uma
  dessas tabelas (acompanhar os portais oficiais).
- Para operações específicas da empresa que não se encaixam na regra
  geral do setor, use data/overrides_operacoes.csv em vez de mexer nas
  tabelas oficiais (ver README).
"""
import argparse
import csv
import datetime as dt
import sys
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHANGELOG = BASE_DIR / "CHANGELOG.md"

# Para cada tipo de tabela: nome do arquivo de saída e mapeamento de
# colunas esperadas (chave interna -> possíveis nomes de coluna no
# arquivo oficial baixado). Ajuste aqui se o layout oficial mudar.
CONFIG_TIPOS: Dict[str, Dict] = {
    "cclasstrib": {
        "arquivo_saida": "cclasstrib_oficial.csv",
        "colunas": {
            "cclasstrib": ["cClassTrib", "CClassTrib", "codigo", "cod_classtrib"],
            "cst": ["CST", "cst"],
            "descricao": ["Descrição", "descricao", "Descricao", "desc_classtrib"],
        },
        "colunas_saida": ["cclasstrib", "cst", "descricao", "versao_it", "fonte"],
    },
    "nbs": {
        "arquivo_saida": "nbs_oficial.csv",
        "colunas": {
            "nbs": ["NBS", "nbs", "codigo_nbs"],
            "descricao": ["Descrição", "descricao", "Descricao"],
            "item_lc116_correlato": ["Item LC116", "item_lc116", "item_lc116_correlato", "LC116"],
        },
        "colunas_saida": ["nbs", "descricao", "item_lc116_correlato", "versao_it", "fonte"],
    },
    "cindop": {
        "arquivo_saida": "cindop_oficial.csv",
        "colunas": {
            "cindop": ["cIndOp", "cindop", "codigo"],
            "descricao": ["Descrição", "descricao", "Descricao"],
        },
        "colunas_saida": ["cindop", "descricao", "versao_it", "fonte"],
    },
    "ctribnac": {
        "arquivo_saida": "ctribnac_oficial.csv",
        "colunas": {
            "ctribnac": ["cTribNac", "ctribnac", "codigo"],
            "descricao": ["Descrição", "descricao", "Descricao"],
            "item_lc116": ["Item LC116", "item_lc116", "LC116"],
            "municipio_iss_devido": [
                "Município ISS devido",
                "municipio_iss_devido",
                "regra_municipio",
            ],
        },
        "colunas_saida": [
            "ctribnac",
            "descricao",
            "item_lc116",
            "municipio_iss_devido",
            "versao_it",
            "fonte",
        ],
    },
}


def _detectar_coluna(cabecalho: List[str], possiveis: List[str]) -> str:
    for nome in possiveis:
        if nome in cabecalho:
            return nome
    raise ValueError(
        f"Nenhuma das colunas esperadas {possiveis} foi encontrada no "
        f"arquivo. Colunas disponíveis: {cabecalho}. Ajuste "
        "CONFIG_TIPOS em sincronizar_tabelas.py se o layout oficial mudou."
    )


def converter_arquivo_oficial(tipo: str, caminho_entrada: Path, versao_it: str) -> int:
    config = CONFIG_TIPOS[tipo]

    with open(caminho_entrada, encoding="utf-8-sig") as f:
        amostra = f.read(4096)
        f.seek(0)
        delimitador = ";" if amostra.count(";") >= amostra.count(",") else ","
        leitor = csv.DictReader(f, delimiter=delimitador)
        cabecalho = leitor.fieldnames or []

        mapa_colunas = {
            chave_interna: _detectar_coluna(cabecalho, possiveis)
            for chave_interna, possiveis in config["colunas"].items()
        }

        linhas_saida = []
        for linha in leitor:
            registro = {
                chave_interna: linha[coluna_real].strip()
                for chave_interna, coluna_real in mapa_colunas.items()
            }
            registro["versao_it"] = versao_it
            registro["fonte"] = "oficial"
            linhas_saida.append(registro)

    caminho_saida = DATA_DIR / config["arquivo_saida"]
    with open(caminho_saida, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=config["colunas_saida"], delimiter=";")
        escritor.writeheader()
        escritor.writerows(linhas_saida)

    _registrar_changelog(tipo, versao_it, len(linhas_saida), config["arquivo_saida"])
    return len(linhas_saida)


def _registrar_changelog(tipo: str, versao_it: str, total_linhas: int, arquivo_saida: str) -> None:
    hoje = dt.date.today().isoformat()
    entrada = (
        f"\n## {hoje} — Sincronização da tabela {tipo}\n"
        f"- Versão/fonte importada: {versao_it}\n"
        f"- Total de códigos importados: {total_linhas}\n"
        f"- Arquivo gerado: data/{arquivo_saida}\n"
    )
    if not CHANGELOG.exists():
        CHANGELOG.write_text("# Changelog\n" + entrada, encoding="utf-8")
    else:
        with open(CHANGELOG, "a", encoding="utf-8") as f:
            f.write(entrada)


def main():
    parser = argparse.ArgumentParser(
        description="Importa tabelas oficiais da Reforma Tributária (cClassTrib, NBS, cIndOp, cTribNac)"
    )
    parser.add_argument(
        "--tipo",
        required=True,
        choices=sorted(CONFIG_TIPOS.keys()),
        help="Qual tabela importar",
    )
    parser.add_argument(
        "--arquivo",
        required=True,
        help="Caminho do CSV oficial baixado manualmente",
    )
    parser.add_argument(
        "--versao-it",
        required=True,
        help='Identificação da versão/fonte importada, ex: "2025.002 v1.60"',
    )
    args = parser.parse_args()

    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        sys.exit(1)

    total = converter_arquivo_oficial(args.tipo, caminho, args.versao_it)
    saida = CONFIG_TIPOS[args.tipo]["arquivo_saida"]
    print(f"OK: {total} códigos importados para data/{saida}")
    print("Não esqueça de commitar o CSV atualizado e o CHANGELOG.md no Git.")


if __name__ == "__main__":
    main()

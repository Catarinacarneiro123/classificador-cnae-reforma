"""
verificar_atualizacoes.py

Verifica, de forma automática, se as tabelas OFICIAIS de cClassTrib e de
Indicadores de Locais de Operação (cIndOp) publicadas pelo Portal da
Conformidade Fácil (SVRS) mudaram desde a última vez que você rodou este
script — sem precisar entrar no portal manualmente toda vez.

Requer a biblioteca "requests" (não vem com o Python puro):
    pip install requests --break-system-packages
    (ou, em ambiente com pip normal: pip install requests)

Uso:
    python src/verificar_atualizacoes.py                # checa tudo
    python src/verificar_atualizacoes.py --tipo cclasstrib
    python src/verificar_atualizacoes.py --tipo cindop

O que o script faz
-------------------
1. Baixa a página HTML pública da tabela (não precisa de certificado
   digital nem login — são páginas públicas de consulta).
2. Extrai os códigos e descrições da tabela, do jeito mais simples e
   robusto possível (procurando os padrões de código de 6 dígitos para
   cClassTrib e as linhas da tabela de cIndOp).
3. Compara com o que está salvo localmente em data/cclasstrib_oficial.csv
   e data/cindop_oficial.csv.
4. Mostra na tela o que mudou: códigos novos, códigos removidos, e
   descrições que mudaram de texto.
5. NÃO sobrescreve os arquivos sozinho — só avisa. Você decide se quer
   atualizar (rodando de novo com --aplicar, que reescreve o CSV local).

Por que não faz isso 100% sozinho sem revisão
-----------------------------------------------
O layout da página pode mudar a qualquer momento (é uma página de
consulta do governo, não uma API estável), e uma mudança de leiaute
pode fazer este script "ler errado" e sobrescrever dados corretos com
lixo. Por isso o padrão é só AVISAR sobre diferenças — use --aplicar
conscientemente, e sempre revise o resultado antes de usar em produção.

Limitações conhecidas
----------------------
- Se o portal mudar de leiaute (deixar de ser uma tabela HTML simples,
  passar a exigir JavaScript para carregar os dados, etc.), este script
  pode parar de funcionar corretamente. Nesse caso, o erro será
  reportado e nada será alterado — ajuste as funções de extração
  (`_extrair_cclasstrib_do_html` / `_extrair_cindop_do_html`) conforme
  o novo formato, ou volte ao fluxo manual do sincronizar_tabelas.py.
- Não verifica NBS nem cTribNac automaticamente, porque essas fontes
  (PDF do MDIC e documentação técnica da NFS-e Nacional) não são
  páginas HTML simples de consulta — para essas, siga o fluxo manual
  descrito no README.
"""
import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

URLS = {
    "cclasstrib": "https://dfe-portal.svrs.rs.gov.br/Cff/ClassificacaoTributaria",
    "cindop": "https://dfe-portal.svrs.rs.gov.br/CFF/TabelaIndicadoresDosLocaisDeOperacao",
}

ARQUIVOS_LOCAIS = {
    "cclasstrib": DATA_DIR / "cclasstrib_oficial.csv",
    "cindop": DATA_DIR / "cindop_oficial.csv",
}


def _importar_requests():
    try:
        import requests  # noqa: F401
        return requests
    except ImportError:
        print(
            "A biblioteca 'requests' não está instalada. Rode:\n"
            "  pip install requests --break-system-packages\n"
            "(ou 'pip install requests', dependendo do seu Python) e tente de novo."
        )
        sys.exit(1)


def _baixar_html(url: str) -> str:
    requests = _importar_requests()
    resposta = requests.get(url, timeout=30)
    resposta.raise_for_status()
    return resposta.text


def _extrair_cclasstrib_do_html(html: str) -> Dict[str, str]:
    """Extrai pares {código: descrição} do HTML da página de cClassTrib.
    Procura o padrão '<código de 6 dígitos> ... <descrição>' de forma
    tolerante ao HTML exato, já que o layout pode variar."""
    texto = re.sub(r"<[^>]+>", " ", html)  # remove tags HTML, deixa só texto
    texto = re.sub(r"\s+", " ", texto)
    resultado: Dict[str, str] = {}
    # Procura sequências "código (6 dígitos) seguido de texto até o próximo código"
    for m in re.finditer(r"\b(\d{6})\b\s+([^\d][^0-9]{5,300}?)(?=\b\d{6}\b|$)", texto):
        codigo, descricao = m.group(1), m.group(2).strip(" .;-")
        if codigo not in resultado and descricao:
            resultado[codigo] = descricao[:300]
    return resultado


def _extrair_cindop_do_html(html: str) -> Dict[str, str]:
    """Extrai pares {código: descrição} do HTML da tabela de cIndOp."""
    texto = re.sub(r"<[^>]+>", " ", html)
    texto = re.sub(r"\s+", " ", texto)
    resultado: Dict[str, str] = {}
    for m in re.finditer(r"\b(\d{6})\b\s+([^\d][^0-9]{5,300}?)(?=\b\d{6}\b|$)", texto):
        codigo, descricao = m.group(1), m.group(2).strip(" .;-")
        if codigo not in resultado and descricao:
            resultado[codigo] = descricao[:300]
    return resultado


EXTRATORES = {
    "cclasstrib": _extrair_cclasstrib_do_html,
    "cindop": _extrair_cindop_do_html,
}


def _ler_local(tipo: str) -> Dict[str, str]:
    caminho = ARQUIVOS_LOCAIS[tipo]
    if not caminho.exists():
        return {}
    chave = tipo  # nome da coluna do código é igual ao tipo
    with open(caminho, encoding="utf-8") as f:
        linhas = [linha for linha in f if not linha.lstrip().startswith("#")]
    leitor = csv.DictReader(linhas, delimiter=";")
    return {linha[chave]: linha.get("descricao", "") for linha in leitor}


def _comparar(local: Dict[str, str], remoto: Dict[str, str]) -> Tuple[List[str], List[str], List[str]]:
    codigos_novos = sorted(set(remoto) - set(local))
    codigos_removidos = sorted(set(local) - set(remoto))
    descricoes_mudaram = sorted(
        codigo for codigo in set(local) & set(remoto)
        if local[codigo].strip() != remoto[codigo].strip()
    )
    return codigos_novos, codigos_removidos, descricoes_mudaram


def verificar(tipo: str, aplicar: bool) -> None:
    print(f"\n--- Verificando {tipo} ---")
    print(f"Baixando: {URLS[tipo]}")
    try:
        html = _baixar_html(URLS[tipo])
    except Exception as e:
        print(f"Não foi possível baixar a página: {e}")
        return

    remoto = EXTRATORES[tipo](html)
    if not remoto:
        print(
            "Não consegui extrair nenhum código do HTML baixado — o layout da "
            "página pode ter mudado. Nada foi alterado. Ajuste a função de "
            f"extração (_extrair_{tipo}_do_html) neste script, ou use o fluxo "
            "manual (sincronizar_tabelas.py)."
        )
        return

    local = _ler_local(tipo)
    novos, removidos, mudaram = _comparar(local, remoto)

    if not novos and not removidos and not mudaram:
        print(f"Nenhuma mudança detectada. {len(remoto)} códigos no total.")
        return

    print(f"Mudanças detectadas (local: {len(local)} códigos, remoto: {len(remoto)} códigos):")
    if novos:
        print(f"  + {len(novos)} código(s) novo(s): {', '.join(novos[:15])}" + (" ..." if len(novos) > 15 else ""))
    if removidos:
        print(f"  - {len(removidos)} código(s) que sumiram localmente: {', '.join(removidos[:15])}" + (" ..." if len(removidos) > 15 else ""))
    if mudaram:
        print(f"  ~ {len(mudaram)} descrição(ões) diferente(s): {', '.join(mudaram[:15])}" + (" ..." if len(mudaram) > 15 else ""))

    if aplicar:
        caminho = ARQUIVOS_LOCAIS[tipo]
        campos = ["cclasstrib", "cst", "descricao", "versao_it", "fonte"] if tipo == "cclasstrib" else \
                 ["cindop", "descricao", "dispositivo_legal", "local", "local_fornecedor", "caracteristica_fornecedor", "versao_it", "fonte"]
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            escritor = csv.DictWriter(f, fieldnames=campos, delimiter=";")
            escritor.writeheader()
            for codigo, descricao in sorted(remoto.items()):
                linha = {c: "" for c in campos}
                linha[tipo] = codigo
                linha["descricao"] = descricao
                if tipo == "cclasstrib":
                    linha["cst"] = codigo[:3]
                linha["versao_it"] = "sincronizado automaticamente via verificar_atualizacoes.py"
                linha["fonte"] = f"oficial - {URLS[tipo]}"
                escritor.writerow(linha)
        print(f"Arquivo {caminho.name} ATUALIZADO. Revise antes de usar em produção e dê commit.")
    else:
        print("Rode de novo com --aplicar para atualizar o arquivo local com esses dados.")


def main():
    parser = argparse.ArgumentParser(
        description="Verifica se as tabelas oficiais de cClassTrib/cIndOp mudaram."
    )
    parser.add_argument(
        "--tipo",
        choices=["cclasstrib", "cindop", "todos"],
        default="todos",
        help="Qual tabela verificar (padrão: todos)",
    )
    parser.add_argument(
        "--aplicar",
        action="store_true",
        help="Sobrescreve o CSV local com os dados baixados agora (revise depois!)",
    )
    args = parser.parse_args()

    tipos = ["cclasstrib", "cindop"] if args.tipo == "todos" else [args.tipo]
    for tipo in tipos:
        verificar(tipo, args.aplicar)


if __name__ == "__main__":
    main()

"""
cli.py

Interface de linha de comando do classificador tributário por CNAE.

MODO INTERATIVO (o mais simples — só rodar e digitar o CNAE):
    python src/cli.py

MODO DIRETO (para scripts/lotes):
    python src/cli.py 8610101
    python src/cli.py 8610101 6920601 4711301
    python src/cli.py 6920601 --municipio "Olinda/PE"
    python src/cli.py --arquivo cnaes.txt   (um CNAE por linha)
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classificador import ClassificadorTributarioCnae  # noqa: E402

LINHA = "=" * 70

# Setores em que o CST pode variar conforme o tipo de contribuinte / estrutura
# societária (art. 127 da LC 214/2025 — profissões intelectuais regulamentadas,
# ex: contabilidade, engenharia, advocacia, arquitetura, administração...)
SETORES_COM_PERGUNTA_SOCIETARIA = {"servicos_profissionais_reduzida", "educacao_fisica_art127"}


def perguntar_dados_societarios(setor: str) -> dict:
    """Pergunta pessoa física/jurídica e, se PJ, os requisitos aplicáveis.
    Setor 'educacao_fisica_art127' tem regra facilitada (só CREF, sem os
    5 requisitos gerais). Retorna kwargs prontos para .classificar()."""
    print()
    print("Este CNAE pode ter CST 200 (redução de 30%) ou CST 000 (tributação")
    print("integral), dependendo da estrutura da empresa (art. 127 da LC 214/2025).")
    if setor == "educacao_fisica_art127":
        print()
        print("Fontes divergem sobre este CNAE (ver docs/CNAES_AMBIGUOS.md). A leitura")
        print("mais defensável: depende da OPERAÇÃO específica, não do CNAE em si.")
        resposta = input(
            "É serviço PESSOAL do profissional (ex: personal trainer) ou acesso "
            "à ESTRUTURA/aulas em grupo (mensalidade de academia)? [pessoal/estrutura/pular]: "
        ).strip().lower()
        if resposta in ("pessoal", "personal", "sim"):
            print()
            resposta_cref = input(
                "A empresa/profissional é fiscalizado(a) pelo CREF? [s/n/pular]: "
            ).strip().lower()
            extras = {"tipo_contribuinte": "pessoal"}
            if resposta_cref in ("s", "sim"):
                extras["atende_requisitos_pj"] = True
            elif resposta_cref in ("n", "nao", "não"):
                extras["atende_requisitos_pj"] = False
            return extras
        if resposta in ("estrutura", "academia", "nao", "não"):
            return {"tipo_contribuinte": "nao"}
        return {}

    tipo = input("O contribuinte é pessoa física ou jurídica? [pf/pj/pular]: ").strip().lower()
    if tipo not in ("pf", "pj"):
        return {}
    if tipo == "pf":
        return {"tipo_contribuinte": "pf"}

    print()
    print("Para pessoa jurídica, TODOS os requisitos abaixo precisam ser verdadeiros")
    print("para manter a redução de 30% (art. 127, §1º, II):")
    print("  1. Sócios têm habilitação ligada ao objeto da sociedade, sob fiscalização do conselho")
    print("  2. A sociedade NÃO tem sócio pessoa jurídica")
    print("  3. A sociedade NÃO é sócia de outra pessoa jurídica")
    print("  4. A sociedade não exerce atividade fora da habilitação dos sócios")
    print("  5. O serviço é prestado diretamente pelos sócios (auxiliares só ajudam)")
    resposta = input("A empresa cumpre TODOS os 5 requisitos acima? [s/n/pular]: ").strip().lower()
    if resposta in ("s", "sim"):
        return {"tipo_contribuinte": "pj", "atende_requisitos_pj": True}
    if resposta in ("n", "nao", "não"):
        return {"tipo_contribuinte": "pj", "atende_requisitos_pj": False}
    return {"tipo_contribuinte": "pj"}


def imprimir_resultado(classificador, cnae, municipio, extras=None, detalhado=False):
    print()
    print(LINHA)
    try:
        resultado = classificador.classificar(cnae, municipio=municipio, **(extras or {}))
        print(resultado.resumo(detalhado=detalhado))
        return resultado
    except ValueError as e:
        print(f"Erro ao processar '{cnae}': {e}")
        return None
    finally:
        print(LINHA)
        print()


def modo_interativo() -> None:
    print(LINHA)
    print("Classificador Tributário por CNAE — modo interativo")
    print(LINHA)
    print()
    classificador = ClassificadorTributarioCnae()

    municipio = input(
        "Município do prestador (Recife/PE, Olinda/PE, Jaboatão dos "
        "Guararapes/PE — ou Enter para pular): "
    ).strip()
    print()
    print("Pronto. Digite um CNAE e aperte Enter.")
    print("Depois de um resultado, digite 'detalhes' para ver tudo daquele CNAE.")
    print("Digite 'sair' para encerrar.")

    ultimo_resultado = None
    ultimo_cnae = None
    ultimo_extras = None

    while True:
        print()
        entrada = input("CNAE> ").strip()
        if not entrada:
            continue
        if entrada.lower() in ("sair", "s", "exit", "quit", "q"):
            print("\nAté mais!")
            break
        if entrada.lower() in ("detalhes", "detalhe", "d"):
            if ultimo_cnae is None:
                print("Nenhum CNAE classificado ainda nesta sessão.")
                continue
            imprimir_resultado(classificador, ultimo_cnae, municipio, ultimo_extras, detalhado=True)
            continue

        cnae = entrada
        extras = {}

        # Pré-checagem rápida do setor para decidir se pergunta PF/PJ
        try:
            pre = classificador.classificar(cnae, municipio=municipio)
            if pre.setor_reforma in SETORES_COM_PERGUNTA_SOCIETARIA:
                extras = perguntar_dados_societarios(pre.setor_reforma)
        except ValueError:
            pass  # deixa o erro aparecer normalmente abaixo

        resultado = imprimir_resultado(classificador, cnae, municipio, extras, detalhado=False)
        ultimo_resultado, ultimo_cnae, ultimo_extras = resultado, cnae, extras


def modo_direto(args: argparse.Namespace) -> None:
    lista = list(args.cnaes)
    if args.arquivo:
        with open(args.arquivo, encoding="utf-8") as f:
            lista += [linha.strip() for linha in f if linha.strip()]

    extras = {}
    if args.tipo_contribuinte:
        extras["tipo_contribuinte"] = args.tipo_contribuinte
    if args.atende_requisitos_pj is not None:
        extras["atende_requisitos_pj"] = args.atende_requisitos_pj

    classificador = ClassificadorTributarioCnae()
    for cnae in lista:
        imprimir_resultado(classificador, cnae, args.municipio, extras, detalhado=args.detalhado)


def main():
    parser = argparse.ArgumentParser(
        description="Classificador tributário (CST/cClassTrib) por CNAE — Reforma Tributária"
    )
    parser.add_argument(
        "cnaes", nargs="*", help="Um ou mais códigos CNAE (com ou sem pontuação)"
    )
    parser.add_argument("--arquivo", help="Arquivo texto com um CNAE por linha")
    parser.add_argument(
        "--municipio",
        default="",
        help='Município do prestador, ex: "Recife/PE", "Olinda/PE", "Jaboatão dos Guararapes/PE".',
    )
    parser.add_argument(
        "--tipo-contribuinte",
        dest="tipo_contribuinte",
        choices=["pf", "pj", "pessoal", "estrutura"],
        default="",
        help="Para profissões intelectuais (art. 127): 'pf' ou 'pj'. Para "
        "educação física (academias): 'pessoal' (personal trainer) ou "
        "'estrutura' (mensalidade/aulas em grupo)",
    )
    parser.add_argument(
        "--atende-requisitos-pj",
        dest="atende_requisitos_pj",
        action="store_true",
        default=None,
        help="Se PJ, informa que a sociedade cumpre os 5 requisitos do art. 127 (mantém redução de 30%%)",
    )
    parser.add_argument(
        "--nao-atende-requisitos-pj",
        dest="atende_requisitos_pj",
        action="store_false",
        help="Se PJ, informa que a sociedade NÃO cumpre os 5 requisitos do art. 127 (CST volta a 000)",
    )
    parser.add_argument(
        "--detalhado",
        action="store_true",
        help="Mostra a saída completa (NBS, cIndOp, cTribNac, todos os alertas)",
    )
    args = parser.parse_args()

    if not args.cnaes and not args.arquivo:
        modo_interativo()
    else:
        modo_direto(args)


if __name__ == "__main__":
    main()

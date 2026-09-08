"""
classificador.py

Núcleo do sistema: recebe um CNAE (classe ou subclasse) e devolve uma
sugestão de classificação tributária para a Reforma Tributária (IBS, CBS
e, quando aplicável, Imposto Seletivo), cobrindo as seis tabelas
envolvidas na emissão de um documento fiscal sob a nova sistemática:

  1. CST (Código de Situação Tributária do IBS/CBS)
  2. cClassTrib (Código de Classificação Tributária — detalha o CST)
  3. NBS (Nomenclatura Brasileira de Serviços — identifica o serviço)
  4. cIndOp (Código Indicador de Operação — característica/local da operação)
  5. cTribNac (Código de Tributação Nacional — identifica o serviço na
     NFS-e Nacional para fins de ISS)
  6. cTribMun (Código de Tributação Municipal — complemento específico
     de cada prefeitura; NÃO tem tabela nacional única)

IMPORTANTE — leia antes de usar em produção
--------------------------------------------
Este sistema entrega uma SUGESTÃO de ponto de partida a partir do CNAE.
A classificação final de cada operação depende da natureza exata dela
(produto/serviço específico, cliente, município, finalidade), não
apenas do CNAE. As tabelas cClassTrib, NBS, cIndOp e cTribNac mudam de
versão com frequência — os arquivos *_seed.csv entregues são EXEMPLOS
ESTRUTURAIS, não a tabela oficial vigente. Sincronize a tabela oficial
(ver sincronizar_tabelas.py) antes de usar isso para emitir notas
fiscais reais. Todo resultado indica se `exige_revisao_manual`.
"""
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional

from modelos import DivisaoCnae, RegraSetor, ResultadoClassificacao, StatusMunicipio

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _ler_csv(caminho: Path) -> List[Dict[str, str]]:
    """Lê um CSV delimitado por ';', ignorando linhas de comentário (iniciadas
    com '#') que alguns arquivos-modelo usam para documentação."""
    if not caminho.exists():
        return []
    with open(caminho, encoding="utf-8") as f:
        linhas_uteis = [linha for linha in f if not linha.lstrip().startswith("#")]
    return list(csv.DictReader(linhas_uteis, delimiter=";"))


def limpar_cnae(cnae: str) -> str:
    """Remove pontuação e mantém só dígitos. Ex: '86.10-1/01' -> '8610101'"""
    return re.sub(r"\D", "", cnae or "")


def extrair_primeiro_codigo(texto: str) -> str:
    """Extrai o primeiro código de 6 dígitos de um texto como
    '200004 ou 200009 ou 200030' -> '200004'. Retorna '' se não achar."""
    m = re.search(r"\b\d{6}\b", texto or "")
    return m.group(0) if m else ""


class ClassificadorTributarioCnae:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.divisoes: Dict[str, DivisaoCnae] = {}
        self.regras: Dict[str, RegraSetor] = {}
        self.cclasstrib: Dict[str, List[str]] = {}
        self.cclasstrib_fonte: str = "nenhuma"
        self.nbs: List[str] = []
        self.nbs_fonte: str = "nenhuma"
        self.cindop: List[str] = []
        self.cindop_fonte: str = "nenhuma"
        self.ctribnac: List[str] = []
        self.ctribnac_fonte: str = "nenhuma"
        self.overrides: Dict[str, Dict[str, str]] = {}
        self._carregar_tabelas()

    def _carregar_tabelas(self) -> None:
        # Divisões CNAE -> setor da reforma
        for linha in _ler_csv(self.data_dir / "cnae_divisoes.csv"):
            self.divisoes[linha["divisao"]] = DivisaoCnae(
                divisao=linha["divisao"],
                descricao_divisao=linha["descricao_divisao"],
                setor_reforma=linha["setor_reforma"],
                observacao_reforma=linha.get("observacao_reforma", ""),
            )

        # Regras por setor -> CST sugerido
        for linha in _ler_csv(self.data_dir / "regras_setor.csv"):
            self.regras[linha["setor_reforma"]] = RegraSetor(
                setor_reforma=linha["setor_reforma"],
                cst_sugerido=linha["cst_sugerido"],
                cclasstrib_sugerido=linha.get("cclasstrib_sugerido", ""),
                percentual_reducao_provavel=linha["percentual_reducao_provavel"],
                base_legal_referencia=linha["base_legal_referencia"],
                nivel_confianca=linha["nivel_confianca"],
                exige_revisao_manual=linha["exige_revisao_manual"].strip().lower()
                in ("sim", "true", "1"),
            )

        # --- cClassTrib: usa a oficial se existir, senão a seed (exemplo) ---
        caminho_oficial = self.data_dir / "cclasstrib_oficial.csv"
        if caminho_oficial.exists():
            caminho_usado, self.cclasstrib_fonte = caminho_oficial, "oficial"
        else:
            caminho_usado, self.cclasstrib_fonte = self.data_dir / "cclasstrib_seed.csv", "seed"
        self.cclasstrib_descricoes: Dict[str, str] = {}
        for linha in _ler_csv(caminho_usado):
            self.cclasstrib.setdefault(linha["cst"], []).append(linha["cclasstrib"])
            self.cclasstrib_descricoes[linha["cclasstrib"]] = linha.get("descricao", "")

        # --- NBS ---
        caminho_oficial = self.data_dir / "nbs_oficial.csv"
        if caminho_oficial.exists():
            caminho_usado, self.nbs_fonte = caminho_oficial, "oficial"
        else:
            caminho_usado, self.nbs_fonte = self.data_dir / "nbs_seed.csv", "seed"
        self.nbs = [linha["nbs"] for linha in _ler_csv(caminho_usado)]

        # --- cIndOp ---
        caminho_oficial = self.data_dir / "cindop_oficial.csv"
        if caminho_oficial.exists():
            caminho_usado, self.cindop_fonte = caminho_oficial, "oficial"
        else:
            caminho_usado, self.cindop_fonte = self.data_dir / "cindop_seed.csv", "seed"
        self.cindop = [linha["cindop"] for linha in _ler_csv(caminho_usado)]

        # --- cTribNac ---
        caminho_oficial = self.data_dir / "ctribnac_oficial.csv"
        if caminho_oficial.exists():
            caminho_usado, self.ctribnac_fonte = caminho_oficial, "oficial"
        else:
            caminho_usado, self.ctribnac_fonte = self.data_dir / "ctribnac_seed.csv", "seed"
        self.ctribnac = [linha["ctribnac"] for linha in _ler_csv(caminho_usado)]

        # Overrides manuais por CNAE específico (operações novas da empresa)
        for linha in _ler_csv(self.data_dir / "overrides_operacoes.csv"):
            self.overrides[limpar_cnae(linha["cnae"])] = linha

        # Exceções por classe CNAE (5 dígitos) — checadas antes da divisão
        self.excecoes_classe: Dict[str, DivisaoCnae] = {}
        for linha in _ler_csv(self.data_dir / "cnae_classes_excecoes.csv"):
            self.excecoes_classe[linha["classe"]] = DivisaoCnae(
                divisao=linha["classe"],
                descricao_divisao=linha["descricao_classe"],
                setor_reforma=linha["setor_reforma"],
                observacao_reforma=linha.get("observacao", ""),
            )

        # Exceções por SUBCLASSE completa (7 dígitos) — checadas antes da
        # classe e da divisão (a mais específica de todas)
        self.excecoes_subclasse: Dict[str, DivisaoCnae] = {}
        for linha in _ler_csv(self.data_dir / "cnae_subclasses_excecoes.csv"):
            self.excecoes_subclasse[linha["cnae"]] = DivisaoCnae(
                divisao=linha["cnae"],
                descricao_divisao=linha["descricao"],
                setor_reforma=linha["setor_reforma"],
                observacao_reforma=linha.get("observacao", ""),
            )

        # Status operacional por município (NFS-e Nacional, alertas práticos)
        self.municipios: Dict[str, StatusMunicipio] = {}
        for linha in _ler_csv(self.data_dir / "municipios_status.csv"):
            chave = linha["municipio"].strip().lower()
            self.municipios[chave] = StatusMunicipio(
                municipio=linha["municipio"],
                codigo_ibge=linha["codigo_ibge"],
                emissor=linha["emissor"],
                alerta_operacional=linha["alerta_operacional"],
                fonte_data_consulta=linha["fonte_data_consulta"],
            )

    def status_municipio(self, nome: str) -> Optional[StatusMunicipio]:
        """Busca o status cadastrado para um município (case-insensitive,
        aceita com ou sem UF). Retorna None se não cadastrado."""
        if not nome:
            return None
        chave = nome.strip().lower()
        if chave in self.municipios:
            return self.municipios[chave]
        # tenta casar ignorando a UF (ex: "Recife" -> "recife/pe")
        for chave_cadastrada, status in self.municipios.items():
            if chave_cadastrada.split("/")[0] == chave.split("/")[0]:
                return status
        return None

    # Requisitos cumulativos do art. 127 da LC 214/2025 para pessoa jurídica
    # ter direito à redução de 30% (cClassTrib 200052). Fonte: LC 214/2025,
    # art. 127, §1º e §2º (consultado em 08/09/2026).
    REQUISITOS_ART127_PJ = [
        "Os sócios têm habilitação profissional ligada ao objeto da sociedade "
        "e estão sob fiscalização do respectivo conselho",
        "A sociedade NÃO tem nenhum sócio pessoa jurídica",
        "A sociedade NÃO é sócia de outra pessoa jurídica",
        "A sociedade não exerce atividade diferente da habilitação dos sócios",
        "O serviço da atividade-fim é prestado diretamente pelos sócios "
        "(auxiliares podem ajudar, mas não substituir)",
    ]

    def classificar(
        self,
        cnae: str,
        municipio: str = "",
        tipo_contribuinte: str = "",       # "pf" ou "pj" — só relevante p/ profissões intelectuais (art. 127)
        atende_requisitos_pj: Optional[bool] = None,
    ) -> ResultadoClassificacao:
        cnae_limpo = limpar_cnae(cnae)
        alertas: List[str] = []

        if not cnae_limpo:
            raise ValueError("CNAE inválido ou vazio.")

        status_mun = self.status_municipio(municipio) if municipio else None
        if municipio and not status_mun:
            alertas.append(
                f"Município '{municipio}' não cadastrado em municipios_status.csv "
                "(sistema hoje cobre Recife/PE, Olinda/PE e Jaboatão dos "
                "Guararapes/PE). Confirme as regras diretamente com a prefeitura."
            )
        elif status_mun:
            alertas.append(
                f"[{status_mun.municipio}] Emissor: {status_mun.emissor}. "
                f"{status_mun.alerta_operacional} (consultado em "
                f"{status_mun.fonte_data_consulta})"
            )

        # 1) Override manual específico da empresa tem prioridade total
        if cnae_limpo in self.overrides:
            ov = self.overrides[cnae_limpo]
            return ResultadoClassificacao(
                cnae_informado=cnae,
                divisao_cnae=cnae_limpo[:2],
                descricao_divisao=ov.get("descricao", "(override manual)"),
                setor_reforma="override_manual",
                observacao_reforma=ov.get("observacao", ""),
                cst_sugerido=ov.get("cst", ""),
                percentual_reducao_provavel=ov.get("percentual_reducao", ""),
                base_legal_referencia=ov.get("base_legal", ""),
                nivel_confianca="alto (definido manualmente pela empresa)",
                exige_revisao_manual=False,
                cclasstrib_candidatos=[],
                cclasstrib_fonte="override",
                cclasstrib_sugerido=ov.get("cclasstrib", ""),
                nbs_candidatos=[ov["nbs"]] if ov.get("nbs") else [],
                nbs_fonte="override",
                cindop_candidatos=[ov["cindop"]] if ov.get("cindop") else [],
                cindop_fonte="override",
                ctribnac_candidatos=[ov["ctribnac"]] if ov.get("ctribnac") else [],
                ctribnac_fonte="override",
                ctribmun_observacao=(
                    f"{ov.get('ctribmun', '(não informado)')} — município: "
                    f"{ov.get('municipio_ctribmun', '(não informado)')}"
                ),
                alertas=alertas + ["Classificação vinda de override manual — revise apenas se a operação mudar."],
            )

        # 2) Busca primeiro por SUBCLASSE completa (7 dígitos), depois por
        # CLASSE (5 dígitos), depois cai para a divisão (2 dígitos) se não
        # houver exceção — do mais específico para o mais genérico
        divisao_cod = cnae_limpo[:2]
        classe_cod = cnae_limpo[:5]
        subclasse_cod = cnae_limpo[:7]
        divisao = self.excecoes_subclasse.get(subclasse_cod)
        if not divisao:
            divisao = self.excecoes_classe.get(classe_cod)
        if not divisao:
            divisao = self.divisoes.get(divisao_cod)
        if not divisao:
            alertas.append(
                f"Divisão CNAE '{divisao_cod}' não encontrada em cnae_divisoes.csv. "
                "Cadastre-a ou complemente a tabela."
            )
            divisao = DivisaoCnae(
                divisao=divisao_cod,
                descricao_divisao="(não cadastrada)",
                setor_reforma="padrao",
                observacao_reforma="Setor não mapeado — tratado como regra geral até revisão.",
            )

        # 3) Busca a regra do setor
        regra = self.regras.get(divisao.setor_reforma)
        if not regra:
            alertas.append(
                f"Setor '{divisao.setor_reforma}' não encontrado em regras_setor.csv."
            )
            regra = RegraSetor(
                setor_reforma=divisao.setor_reforma,
                cst_sugerido="000",
                percentual_reducao_provavel="não identificado",
                base_legal_referencia="a definir",
                nivel_confianca="baixo",
                exige_revisao_manual=True,
            )

        # 4) Código cClassTrib específico sugerido pela regra do setor
        #    (ex: "200029" ou "200004 ou 200009 ou 200030" -> pega o primeiro
        #    e sinaliza que há mais de uma opção a confirmar)
        cclasstrib_sugerido_raw = regra.cclasstrib_sugerido or ""
        if divisao.setor_reforma == "ensino_esportes_ambiguo":
            alertas.append(
                "CNAE AMBÍGUO: este código (ensino de esportes, ex.: escolinha de "
                "natação) pode seguir a redução de 60% da educação (art. 129, "
                "Anexo II, cClassTrib 200028) OU a de 30% de profissional de "
                "educação física (art. 127, X, cClassTrib 200052) — não "
                "encontramos fonte que resolva isso com certeza. Recomendamos "
                "confirmar com orientação da Receita Federal/Comitê Gestor do "
                "IBS antes de aplicar em nota fiscal, e cadastrar a decisão em "
                "overrides_operacoes.csv depois de confirmada."
            )
        cclasstrib_sugerido = extrair_primeiro_codigo(cclasstrib_sugerido_raw)
        cst_final = regra.cst_sugerido
        percentual_final = regra.percentual_reducao_provavel
        base_legal_final = regra.base_legal_referencia
        enquadramento_societario = ""

        # 4.1) Regra especial do art. 127 da LC 214/2025 (profissões intelectuais
        # regulamentadas, ex: contabilidade, engenharia, advocacia, arquitetura):
        # pessoa jurídica só tem direito à redução de 30% se cumprir 5 requisitos
        # cumulativos. Se não cumprir, a tributação volta a ser integral (CST 000).
        if divisao.setor_reforma == "servicos_profissionais_reduzida":
            tipo = tipo_contribuinte.strip().lower()
            if tipo == "pf":
                enquadramento_societario = (
                    "Pessoa física — redução de 30% se o serviço prestado estiver "
                    "vinculado à habilitação profissional (art. 127, §1º, I)."
                )
            elif tipo == "pj":
                if atende_requisitos_pj is True:
                    enquadramento_societario = (
                        "Pessoa jurídica que atende aos 5 requisitos cumulativos "
                        "do art. 127, §1º, II — mantém a redução de 30%."
                    )
                elif atende_requisitos_pj is False:
                    cst_final = "000"
                    cclasstrib_sugerido = "000001"
                    percentual_final = "0% (tributação integral)"
                    base_legal_final = (
                        "LC 214/2025, art. 127, §1º, II — a sociedade NÃO cumpre "
                        "todos os 5 requisitos cumulativos, então perde a redução "
                        "de 30% e volta à tributação integral (CST 000)"
                    )
                    enquadramento_societario = (
                        "Pessoa jurídica que NÃO atende a pelo menos um dos 5 "
                        "requisitos do art. 127, §1º, II — perde a redução de 30% "
                        "inteira, não parcialmente."
                    )
                    alertas.append(
                        "Sociedade não cumpre os requisitos do art. 127 -> este "
                        "CNAE volta para CST 000 (tributação integral) em vez do "
                        "CST 200/cClassTrib 200052."
                    )
                else:
                    alertas.append(
                        "Pessoa jurídica de profissão intelectual regulamentada: a "
                        "redução de 30% (CST 200/200052) só vale se a sociedade "
                        "cumprir TODOS os 5 requisitos do art. 127, §1º, II da LC "
                        "214/2025: " + " | ".join(self.REQUISITOS_ART127_PJ) +
                        ". Informe se a empresa atende para confirmar o CST correto."
                    )
            else:
                alertas.append(
                    "Este CNAE pode ter CST 200 (redução de 30%, cClassTrib "
                    "200052) OU CST 000 (tributação integral), dependendo de a "
                    "empresa ser pessoa física ou de a sociedade cumprir os 5 "
                    "requisitos do art. 127 da LC 214/2025 (nenhum sócio PJ, não "
                    "ser sócia de outra PJ, sócios com habilitação na área, "
                    "atividade exclusiva da habilitação, serviço prestado "
                    "diretamente pelos sócios). Informe tipo_contribuinte='pf' ou "
                    "'pj' (+ atende_requisitos_pj) para confirmar."
                )

        # 4.2) Educação física (art. 127, X e §3º): a pessoa jurídica é
        # DISPENSADA dos 5 requisitos — só precisa estar fiscalizada pelo
        # CREF. Reaproveita o parâmetro atende_requisitos_pj para representar
        # "está registrada/fiscalizada pelo CREF?".
        elif divisao.setor_reforma == "educacao_fisica_art127":
            # A partir de dois artigos que se contradizem sobre este ponto
            # (um diz que academia/crossfit/pilates como estabelecimento é
            # sempre tributação integral; outro diz que a pessoa jurídica
            # de educação física tem a redução via §3º do art. 127), a leitura
            # mais defensável é que isso depende da OPERAÇÃO: serviço pessoal
            # do profissional (personal trainer) x acesso à estrutura/aulas em
            # grupo (mensalidade de academia). Ver docs/CNAES_AMBIGUOS.md.
            servico_pessoal = tipo_contribuinte.strip().lower()  # reaproveita o param como "sim"/"nao"/"" aqui
            if servico_pessoal in ("sim", "pessoal", "personal"):
                cclasstrib_sugerido = "200052"
                if atende_requisitos_pj is False:
                    cst_final = "000"
                    cclasstrib_sugerido = "000001"
                    percentual_final = "0% (tributação integral)"
                    base_legal_final = (
                        "LC 214/2025, art. 127 — sem fiscalização do CREF "
                        "confirmada, sem direito à redução de 30%"
                    )
                    enquadramento_societario = "Serviço pessoal, mas SEM fiscalização do CREF confirmada."
                else:
                    cst_final = "200"
                    percentual_final = "30%"
                    base_legal_final = (
                        "LC 214/2025, art. 127, X e §3º - serviço pessoal do "
                        "profissional de educação física, fiscalizado pelo CREF"
                    )
                    enquadramento_societario = (
                        "Serviço pessoal do profissional de educação física "
                        "(ex: personal trainer) — redução de 30%, com dispensa "
                        "dos 5 requisitos de PJ pelo §3º, desde que fiscalizado "
                        "pelo CREF."
                    )
            elif servico_pessoal in ("nao", "não", "estrutura", "academia"):
                cst_final = "000"
                cclasstrib_sugerido = "000001"
                percentual_final = "0% (tributação integral)"
                base_legal_final = (
                    "Acesso à estrutura/aulas em grupo (mensalidade de "
                    "academia) — não é serviço pessoal do profissional, "
                    "tratado como tributação integral"
                )
                enquadramento_societario = "Acesso à estrutura/aulas em grupo — CST 000 (tributação integral)."
            else:
                cst_final = "000"
                cclasstrib_sugerido = "000001"
                percentual_final = "0% (padrão) — pode ser 30% em caso específico"
                base_legal_final = "LC 214/2025 - regra geral, até confirmação da natureza da operação"
                alertas.append(
                    "AMBÍGUO: fontes divergem sobre este CNAE. Uma leitura do "
                    "art. 127, X e §3º dá 30% de redução (cClassTrib 200052) "
                    "para SERVIÇO PESSOAL do profissional de educação física "
                    "(ex: personal trainer) fiscalizado pelo CREF. Mas o acesso "
                    "genérico à estrutura da academia (mensalidade, aulas em "
                    "grupo) tende a ser tributação integral (CST 000) por não "
                    "constar nas listas de regime diferenciado. O sistema "
                    "assume CST 000 por padrão até você confirmar qual é a "
                    "operação — veja docs/CNAES_AMBIGUOS.md."
                )
                enquadramento_societario = (
                    "Sem confirmação da operação — assumido CST 000 por padrão."
                )

        if " ou " in cclasstrib_sugerido_raw and cst_final == regra.cst_sugerido:
            alertas.append(
                f"Há mais de um cClassTrib possível para este setor "
                f"('{cclasstrib_sugerido_raw}') — escolha o exato conforme o "
                f"produto/serviço da operação."
            )
        if cclasstrib_sugerido and cclasstrib_sugerido not in self.cclasstrib_descricoes and self.cclasstrib_fonte == "oficial":
            alertas.append(
                f"O código sugerido {cclasstrib_sugerido} não foi encontrado na "
                f"tabela oficial carregada — pode ter sido descontinuado em "
                f"versão mais recente. Confirme no portal oficial."
            )
        elif cclasstrib_sugerido and self.cclasstrib_fonte == "oficial":
            descricao_oficial = self.cclasstrib_descricoes.get(cclasstrib_sugerido, "")
            if descricao_oficial:
                alertas.append(f"Descrição oficial de {cclasstrib_sugerido}: {descricao_oficial}")

        # 5) Busca demais candidatos de cClassTrib do mesmo CST, como alternativa
        cst_principal = cst_final.split(" ")[0].strip(",")
        candidatos_cclasstrib = [
            c for c in self.cclasstrib.get(cst_principal, []) if c != cclasstrib_sugerido
        ]
        if not candidatos_cclasstrib and not cclasstrib_sugerido:
            alertas.append(
                f"Nenhum cClassTrib cadastrado localmente para o CST {cst_principal}. "
                "Rode a sincronização (src/sincronizar_tabelas.py --tipo cclasstrib)."
            )
        elif self.cclasstrib_fonte == "seed":
            alertas.append(
                "cClassTrib vindo da tabela SEED (exemplo) — sincronize a tabela "
                "oficial antes de usar em produção."
            )

        alertas.append(
            "NBS, cIndOp e cTribNac NÃO são sugeridos automaticamente a partir do "
            "CNAE: eles dependem do serviço/operação específica prestada (item da "
            "LC 116, característica da operação), não da atividade econômica em si. "
            "Consulte a tabela oficial correspondente e, se for uma operação "
            "recorrente da empresa, cadastre o resultado em "
            "data/overrides_operacoes.csv para reaproveitar depois."
        )
        if self.nbs_fonte == "seed":
            alertas.append(
                "Tabela NBS local é apenas EXEMPLO — importe a tabela oficial "
                "(Portal Nacional da NFS-e) para identificar a NBS correta do serviço."
            )
        if self.cindop_fonte == "seed":
            alertas.append(
                "Tabela cIndOp local é apenas EXEMPLO — importe o Anexo VII oficial "
                "da NFS-e Nacional."
            )
        if self.ctribnac_fonte == "seed":
            alertas.append(
                "Tabela cTribNac local é apenas EXEMPLO — importe a tabela oficial "
                "de 338 códigos da NFS-e Nacional."
            )

        if regra.nivel_confianca in ("medio", "baixo") and cst_final == regra.cst_sugerido:
            alertas.append(
                "Este setor tem regra de exceção/redução na reforma: confirme o "
                "enquadramento exato do produto/serviço antes de aplicar em nota fiscal."
            )

        return ResultadoClassificacao(
            cnae_informado=cnae,
            divisao_cnae=divisao_cod,
            descricao_divisao=divisao.descricao_divisao,
            setor_reforma=divisao.setor_reforma,
            observacao_reforma=divisao.observacao_reforma,
            cst_sugerido=cst_final,
            percentual_reducao_provavel=percentual_final,
            base_legal_referencia=base_legal_final,
            nivel_confianca=regra.nivel_confianca,
            exige_revisao_manual=regra.exige_revisao_manual,
            cclasstrib_candidatos=candidatos_cclasstrib,
            cclasstrib_fonte=self.cclasstrib_fonte,
            cclasstrib_sugerido=cclasstrib_sugerido,
            nbs_candidatos=[],  # NBS depende do serviço específico prestado, não só do CNAE
            nbs_fonte=self.nbs_fonte,
            cindop_candidatos=[],  # cIndOp depende da característica da operação, não só do CNAE
            cindop_fonte=self.cindop_fonte,
            ctribnac_candidatos=[],  # cTribNac depende do serviço específico (item LC 116)
            ctribnac_fonte=self.ctribnac_fonte,
            enquadramento_societario=enquadramento_societario,
            alertas=alertas,
        )

    def classificar_lote(self, lista_cnaes: List[str]) -> List[ResultadoClassificacao]:
        return [self.classificar(c) for c in lista_cnaes]

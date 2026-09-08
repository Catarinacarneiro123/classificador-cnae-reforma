"""
Modelos de dados usados pelo classificador tributário por CNAE.
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RegraSetor:
    setor_reforma: str
    cst_sugerido: str
    cclasstrib_sugerido: str
    percentual_reducao_provavel: str
    base_legal_referencia: str
    nivel_confianca: str
    exige_revisao_manual: bool


@dataclass
class StatusMunicipio:
    municipio: str
    codigo_ibge: str
    emissor: str
    alerta_operacional: str
    fonte_data_consulta: str


@dataclass
class DivisaoCnae:
    divisao: str
    descricao_divisao: str
    setor_reforma: str
    observacao_reforma: str


@dataclass
class ResultadoClassificacao:
    cnae_informado: str
    divisao_cnae: str
    descricao_divisao: str
    setor_reforma: str
    observacao_reforma: str
    cst_sugerido: str
    percentual_reducao_provavel: str
    base_legal_referencia: str
    nivel_confianca: str
    exige_revisao_manual: bool
    cclasstrib_candidatos: List[str] = field(default_factory=list)
    cclasstrib_fonte: str = "nenhuma"          # "oficial", "seed" ou "nenhuma"
    cclasstrib_sugerido: str = ""              # código específico mais provável (não só o grupo do CST)
    nbs_candidatos: List[str] = field(default_factory=list)
    nbs_fonte: str = "nenhuma"
    cindop_candidatos: List[str] = field(default_factory=list)
    cindop_fonte: str = "nenhuma"
    ctribnac_candidatos: List[str] = field(default_factory=list)
    ctribnac_fonte: str = "nenhuma"
    ctribmun_observacao: str = (
        "Não calculado automaticamente — depende do município. Consulte "
        "data/ctribmun/<municipio>.csv ou cadastre em overrides_operacoes.csv."
    )
    enquadramento_societario: str = ""  # preenchido só quando relevante (art. 127 - profissões intelectuais)
    alertas: List[str] = field(default_factory=list)

    def resumo(self, detalhado: bool = False) -> str:
        if not detalhado:
            return self._resumo_curto()
        return self._resumo_detalhado()

    def _resumo_curto(self) -> str:
        L = []
        L.append(f"CNAE {self.cnae_informado} — {self.descricao_divisao}")
        L.append("")
        L.append(f"CST: {self.cst_sugerido}   cClassTrib: {self.cclasstrib_sugerido or '(não identificado)'}")
        L.append(f"Redução: {self.percentual_reducao_provavel}")
        L.append(f"Base legal: {self.base_legal_referencia}")
        if self.enquadramento_societario:
            L.append(f"Situação societária: {self.enquadramento_societario}")
        L.append(f"Revisar manualmente: {'SIM' if self.exige_revisao_manual else 'não'}")
        if self.alertas:
            L.append("")
            L.append(f"⚠ {len(self.alertas)} alerta(s) — digite 'detalhes' para ver tudo (NBS, cIndOp, cTribNac, avisos completos).")
        return "\n".join(L)

    def _resumo_detalhado(self) -> str:
        L = []

        L.append(f"CNAE informado: {self.cnae_informado}")
        L.append(f"Divisão CNAE:   {self.divisao_cnae} - {self.descricao_divisao}")
        L.append(f"Setor (reforma): {self.setor_reforma}")
        L.append("")

        L.append("--- CST / cClassTrib (IBS e CBS) ---")
        L.append(f"CST sugerido: {self.cst_sugerido}")
        L.append(f"cClassTrib sugerido (específico): {self.cclasstrib_sugerido or '(não identificado)'}")
        L.append(self._linha_candidatos("Demais cClassTrib do mesmo CST", self.cclasstrib_candidatos, self.cclasstrib_fonte))
        L.append(f"Redução/observação: {self.percentual_reducao_provavel}")
        L.append(f"Base legal de referência: {self.base_legal_referencia}")
        if self.enquadramento_societario:
            L.append(f"Situação societária: {self.enquadramento_societario}")
        L.append(f"Nível de confiança da sugestão: {self.nivel_confianca}")
        L.append(f"Exige revisão manual: {'SIM' if self.exige_revisao_manual else 'não'}")
        L.append("")

        L.append("--- NBS / cIndOp / cTribNac (identificação do serviço) ---")
        L.append(self._linha_candidatos("NBS", self.nbs_candidatos, self.nbs_fonte))
        L.append(self._linha_candidatos("cIndOp", self.cindop_candidatos, self.cindop_fonte))
        L.append(self._linha_candidatos("cTribNac", self.ctribnac_candidatos, self.ctribnac_fonte))
        L.append("")

        L.append("--- cTribMun (municipal) ---")
        L.append(self.ctribmun_observacao)

        if self.alertas:
            L.append("")
            L.append("--- Alertas ---")
            for alerta in self.alertas:
                L.append(f"• {alerta}")

        return "\n".join(L)

    @staticmethod
    def _linha_candidatos(nome: str, candidatos: List[str], fonte: str) -> str:
        if not candidatos:
            return (
                f"{nome} candidatos: nenhum na tabela local — sincronize a "
                f"tabela oficial (ver src/sincronizar_tabelas.py --tipo "
                f"{nome.lower()})"
            )
        marcador = {
            "oficial": "[tabela oficial sincronizada]",
            "seed": "[EXEMPLO — NÃO usar em produção, sincronize a tabela oficial]",
        }.get(fonte, "")
        if len(candidatos) > 6:
            amostra = ", ".join(candidatos[:6])
            return f"{nome}: {amostra}, ... (+{len(candidatos) - 6} outros no mesmo grupo) {marcador}".strip()
        return f"{nome}: {', '.join(candidatos)} {marcador}".strip()

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from classificador import ClassificadorTributarioCnae, limpar_cnae  # noqa: E402


def test_limpar_cnae():
    assert limpar_cnae("86.10-1/01") == "8610101"
    assert limpar_cnae("6920-6/01") == "6920601"


def test_classificar_saude():
    c = ClassificadorTributarioCnae()
    r = c.classificar("8610101")
    assert r.divisao_cnae == "86"
    assert r.setor_reforma == "saude_reduzida"
    assert r.cst_sugerido == "200"
    assert r.cclasstrib_sugerido == "200029"  # código oficial real, confirmado no portal SVRS
    assert r.exige_revisao_manual is True
    # NBS/cIndOp/cTribNac não são derivados do CNAE — devem vir vazios
    # até serem preenchidos via override ou tabela oficial sincronizada
    assert r.nbs_candidatos == []
    assert r.ctribnac_candidatos == []


def test_classificar_contabilidade():
    c = ClassificadorTributarioCnae()
    r = c.classificar("6920601")
    # Este CNAE tem um override cadastrado (é o CNAE principal da empresa)
    assert r.setor_reforma == "override_manual"
    assert r.cst_sugerido == "200"
    assert r.cclasstrib_sugerido == "200052"  # "Prestação de serviços de profissões intelectuais"
    assert r.nbs_candidatos == ["1.1302.21.00"]  # "Serviços de contabilidade" (NBS oficial real)


def test_classificar_padrao():
    c = ClassificadorTributarioCnae()
    r = c.classificar("4711302")
    assert r.setor_reforma == "padrao"
    assert r.cst_sugerido == "000"


def test_divisao_desconhecida_nao_quebra():
    c = ClassificadorTributarioCnae()
    r = c.classificar("00000000")
    assert r.divisao_cnae == "00"
    assert len(r.alertas) >= 1


def test_override_manual_tem_prioridade():
    c = ClassificadorTributarioCnae()
    # simula um override em memória
    c.overrides["8610101"] = {
        "cnae": "8610101",
        "descricao": "Clínica com regra própria",
        "cst": "200",
        "cclasstrib": "200099",
        "percentual_reducao": "100%",
        "base_legal": "Definição interna revisada",
        "nbs": "1.0101",
        "cindop": "01",
        "ctribnac": "171901",
        "ctribmun": "001",
        "municipio_ctribmun": "Paulista/PE",
        "observacao": "Override de teste",
    }
    r = c.classificar("86.10-1/01")
    assert r.setor_reforma == "override_manual"
    assert r.cst_sugerido == "200"
    assert r.nbs_candidatos == ["1.0101"]
    assert "Paulista/PE" in r.ctribmun_observacao


def test_municipio_olinda_alerta():
    c = ClassificadorTributarioCnae()
    r = c.classificar("4711302", municipio="Olinda/PE")
    assert any("Olinda" in a and "NBS" in a for a in r.alertas)


def test_municipio_nao_cadastrado():
    c = ClassificadorTributarioCnae()
    r = c.classificar("4711302", municipio="São Paulo/SP")
    assert any("não cadastrado" in a for a in r.alertas)


def test_art127_engenharia_pj_nao_atende_vira_cst_000():
    c = ClassificadorTributarioCnae()
    r = c.classificar("7112000", tipo_contribuinte="pj", atende_requisitos_pj=False)
    assert r.cst_sugerido == "000"
    assert r.cclasstrib_sugerido == "000001"


def test_art127_engenharia_pj_atende_mantem_cst_200():
    c = ClassificadorTributarioCnae()
    r = c.classificar("7112000", tipo_contribuinte="pj", atende_requisitos_pj=True)
    assert r.cst_sugerido == "200"
    assert r.cclasstrib_sugerido == "200052"


def test_art127_pessoa_fisica_mantem_cst_200():
    c = ClassificadorTributarioCnae()
    r = c.classificar("7112000", tipo_contribuinte="pf")
    assert r.cst_sugerido == "200"


def test_resumo_curto_por_padrao_e_detalhado_sob_pedido():
    c = ClassificadorTributarioCnae()
    r = c.classificar("8610101")
    curto = r.resumo()
    detalhado = r.resumo(detalhado=True)
    assert len(curto) < len(detalhado)
    assert "CST:" in curto
    assert "--- CST / cClassTrib" in detalhado


def test_condicionamento_fisico_usa_excecao_de_classe_art127():
    c = ClassificadorTributarioCnae()
    r = c.classificar("9313100")
    assert r.setor_reforma == "educacao_fisica_art127"
    # Sem confirmar a operação, o sistema assume o caminho mais conservador
    # (CST 000) por causa da ambiguidade documentada em CNAES_AMBIGUOS.md
    assert r.cst_sugerido == "000"
    assert any("AMBÍGUO" in a for a in r.alertas)


def test_condicionamento_fisico_pj_sem_cref_vira_cst_000():
    c = ClassificadorTributarioCnae()
    r = c.classificar("9313100", tipo_contribuinte="estrutura")
    assert r.cst_sugerido == "000"


def test_condicionamento_fisico_pj_com_cref_mantem_cst_200():
    c = ClassificadorTributarioCnae()
    r = c.classificar("9313100", tipo_contribuinte="pessoal", atende_requisitos_pj=True)
    assert r.cst_sugerido == "200"
    assert r.cclasstrib_sugerido == "200052"


def test_agronomia_subclasse_usa_art127():
    c = ClassificadorTributarioCnae()
    r = c.classificar("7490103")
    assert r.setor_reforma == "servicos_profissionais_reduzida"
    assert r.cst_sugerido == "200"


def test_traducao_mesma_classe_da_agronomia_fica_padrao():
    c = ClassificadorTributarioCnae()
    r = c.classificar("7490101")
    assert r.setor_reforma == "padrao"
    assert r.cst_sugerido == "000"


def test_ensino_de_esportes_fica_marcado_como_ambiguo():
    c = ClassificadorTributarioCnae()
    r = c.classificar("8591100")
    assert r.setor_reforma == "ensino_esportes_ambiguo"
    assert any("AMBÍGUO" in a for a in r.alertas)


if __name__ == "__main__":
    test_limpar_cnae()
    test_classificar_saude()
    test_classificar_contabilidade()
    test_classificar_padrao()
    test_divisao_desconhecida_nao_quebra()
    test_override_manual_tem_prioridade()
    test_municipio_olinda_alerta()
    test_municipio_nao_cadastrado()
    test_art127_engenharia_pj_nao_atende_vira_cst_000()
    test_art127_engenharia_pj_atende_mantem_cst_200()
    test_art127_pessoa_fisica_mantem_cst_200()
    test_resumo_curto_por_padrao_e_detalhado_sob_pedido()
    test_condicionamento_fisico_usa_excecao_de_classe_art127()
    test_condicionamento_fisico_pj_sem_cref_vira_cst_000()
    test_condicionamento_fisico_pj_com_cref_mantem_cst_200()
    test_agronomia_subclasse_usa_art127()
    test_traducao_mesma_classe_da_agronomia_fica_padrao()
    test_ensino_de_esportes_fica_marcado_como_ambiguo()
    print("Todos os testes passaram.")

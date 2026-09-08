# Changelog

Este arquivo registra:
- Toda vez que a tabela oficial cClassTrib/CST for sincronizada (via
  `src/sincronizar_tabelas.py`, que já grava aqui automaticamente).
- Toda vez que uma nova operação/CNAE for adicionada manualmente em
  `data/overrides_operacoes.csv` (registre à mão, seguindo o modelo abaixo).

## 2026-09-08 — Histórico legislativo da academia (art. 127 x art. 141) documentado
- Encontrada uma apresentação de junho/2024 da ACAD (associação das
  academias) ao Grupo de Trabalho da Câmara dos Deputados sobre o PLP
  68/2024, mostrando que a indústria reclamou de ficar de fora da
  redução de 60% de "atividades desportivas" (art. 141) — pedido não
  atendido, confirmado pela ausência de um terceiro código na tabela
  oficial real (só existem 200041 e 200042, para os incisos I e II).
  Isso descarta a hipótese de a academia seguir a regra de 60%.
- A mesma apresentação mostra que a exigência de "sociedade de união
  de profissionais" (pré-§3º) deixaria a maioria das academias fora da
  redução de 30% também — o que sugere que o §3º do art. 127 (que
  dispensa essa exigência para PJ de educação física fiscalizada pelo
  CREF) foi possivelmente adicionado depois para resolver esse
  problema, mas isso é inferência histórica, não confirmação direta.
- Documentado em `docs/CNAES_AMBIGUOS.md`, mantendo a mesma cautela do
  sistema (CST 000 por padrão, pergunta ao usuário) — a nova evidência
  reforça a hipótese do CST 200/30% em detrimento da tributação
  integral, mas não chega a ser confirmação suficiente para mudar o
  comportamento padrão do sistema.

## 2026-09-08 — Correção importante: academia (9313-1/00) volta a ser AMBÍGUA, não 30% garantido
- Um artigo de terceiros (hopecont.com), enviado pela usuária, afirma
  que "Academia, CrossFit, estúdio de pilates" são **tributados
  integralmente**, contradizendo diretamente a conclusão anterior deste
  projeto (CST 200/30% via art. 127, X e §3º).
- Não foi possível encontrar uma fonte oficial que resolva esse
  conflito diretamente (não localizamos a correlação NBS → cClassTrib
  oficial específica para "atividades de condicionamento físico"). A
  leitura adotada — que concilia as duas fontes em vez de descartar uma
  delas — é que a resposta correta **depende da operação especifica**,
  não do CNAE: serviço pessoal do profissional (personal trainer,
  fiscalizado pelo CREF) tende a ter a redução de 30%; acesso à
  estrutura/aulas em grupo (mensalidade de academia) tende a ser
  tributação integral.
- **Mudança de comportamento**: o sistema agora assume **CST 000 por
  padrão** (mais conservador) para este CNAE até o usuário confirmar
  qual é a operação, em vez de assumir 30% por padrão como antes.
- `cli.py`: a pergunta interativa para este CNAE mudou de "é PJ e
  cumpre os requisitos?" para "é serviço pessoal do profissional ou
  acesso à estrutura?" (mais direto ao ponto da ambiguidade real).
- Documentado detalhadamente em `docs/CNAES_AMBIGUOS.md`, incluindo o
  histórico da própria correção deste projeto sobre o assunto.

## 2026-09-08 — Tabela cIndOp real completa, revisão de CNAEs ambíguos e verificação automática
- **cIndOp**: substituído o exemplo pela tabela oficial completa e real
  (39 códigos), extraída ao vivo da "Tabela de Indicadores dos Locais
  de Operação" do Portal da Conformidade Fácil (SVRS):
  `https://dfe-portal.svrs.rs.gov.br/CFF/TabelaIndicadoresDosLocaisDeOperacao`
- **Revisão de CNAEs ambíguos/mal-classificados** (documentada em
  `docs/CNAES_AMBIGUOS.md`):
  - Corrigido: divisão 74 (outras atividades profissionais) estava
    marcada inteira como profissão regulamentada (30%) — na verdade é
    muito heterogênea (design, fotografia, tradução) e a maioria não
    está no art. 127. Voltou para regra padrão, com exceções pontuais.
  - Corrigido: CNAE 7490-1/03 (agronomia) mantém a redução de 30% (art.
    127, XI), mas agora via exceção por SUBCLASSE completa (7 dígitos),
    sem afetar as demais subclasses da mesma classe (tradução,
    agenciamento, etc., que voltaram para CST 000).
  - Documentado como AMBÍGUO, sem resolução encontrada: CNAE 8591-1/00
    (ensino de esportes, inclui escolinhas de natação) — pode seguir a
    redução de educação (60%, art. 129) ou de educação física (30%,
    art. 127, X). O sistema sinaliza os dois cClassTrib possíveis com
    alerta em vez de escolher um sozinho.
- Adicionado `data/cnae_subclasses_excecoes.csv`: exceções por CNAE
  completo (7 dígitos), checadas antes da classe (5 dígitos) e da
  divisão (2 dígitos) — resolve casos em que uma classe mistura
  atividades com tratamento tributário bem diferente.
- Criado `src/verificar_atualizacoes.py`: script que baixa as páginas
  públicas de cClassTrib e cIndOp do Portal da Conformidade Fácil,
  compara com os CSVs locais e avisa o que mudou (não sobrescreve
  sozinho, a menos que rodado com `--aplicar`). Requer `pip install
  requests`. **Não foi possível testar de ponta a ponta** no ambiente
  onde este projeto foi criado (sem acesso a sites do governo
  brasileiro) — testar antes de confiar no resultado.

## 2026-09-08 — Correção: CNAE 9313-1/00 (academias) usa art. 127 facilitado, não a regra de esporte/cultura
- Confirmado o texto do **§3º do art. 127 da LC 214/2025**: "Não se
  aplicam os §§ 1º e 2º deste artigo à prestação de serviços
  relacionada à profissão do inciso X do caput deste artigo
  [profissionais de educação física] efetuada por pessoa jurídica,
  desde que submetida à fiscalização de conselho profissional."
- Isso corrige um erro do sistema: o CNAE **9313-1/00** (atividades de
  condicionamento físico — academias, personal trainers, pilates,
  crossfit, hidroginástica) estava caindo na regra genérica da divisão
  93 (esportes/recreação, 60% de redução via art. 141), quando na
  verdade segue o **art. 127, X** (educação física, **30%** de
  redução, cClassTrib **200052**) — com a vantagem de que a pessoa
  jurídica é **dispensada dos 5 requisitos gerais**, bastando estar
  fiscalizada pelo CREF.
- Criado `data/cnae_classes_excecoes.csv`: uma tabela de exceções por
  **classe CNAE** (5 dígitos), checada *antes* da regra por divisão (2
  dígitos), para casos como esse em que uma classe específica foge do
  padrão do resto da divisão. Reaproveitável para futuras exceções
  parecidas.
- `classificador.py` ganhou um novo setor `educacao_fisica_art127`
  com pergunta interativa própria (só CREF, sem os 5 requisitos).

## 2026-09-08 — Regra do art. 127 (CST 200 x 000 por tipo de sociedade) e saída enxuta
- Pesquisada e implementada a regra do **art. 127 da LC 214/2025**: a
  redução de 30% (CST 200, cClassTrib 200052) para as 18 profissões
  intelectuais regulamentadas (engenharia, contabilidade, advocacia,
  arquitetura, administração, etc.) depende de:
  - Pessoa física: sempre mantém a redução, se o serviço estiver
    vinculado à habilitação profissional.
  - Pessoa jurídica: só mantém a redução se cumprir **todos** os 5
    requisitos cumulativos do §1º, II (nenhum sócio PJ, não ser sócia
    de PJ, sócios com habilitação na área, atividade exclusiva da
    habilitação, serviço prestado diretamente pelos sócios). Se faltar
    algum requisito, o sistema agora ajusta a sugestão para **CST 000
    (tributação integral)** em vez de manter erroneamente o CST 200.
  - Documentada a exceção de médicos (ficam no regime de saúde, 60% de
    redução, mais vantajoso) e de educação física (dispensada dos
    requisitos de PJ pelo §3º).
- `classificar()` ganhou os parâmetros `tipo_contribuinte` ("pf"/"pj")
  e `atende_requisitos_pj` (bool). O modo interativo do `cli.py` agora
  pergunta isso automaticamente quando o CNAE cai num setor de
  profissão intelectual regulamentada.
- **Saída reformulada para ser mais enxuta**: por padrão, o resultado
  mostra só CST, cClassTrib, % de redução, base legal e situação
  societária (quando relevante) — a versão completa (NBS, cIndOp,
  cTribNac, todos os alertas) só aparece com `--detalhado` (modo
  direto) ou digitando `detalhes` depois de um resultado (modo
  interativo).

## 2026-09-08 — Modo interativo e saída mais legível
- `cli.py` ganhou modo interativo: rodar `python src/cli.py` sem nada
  na frente entra num loop que pergunta o município (uma vez, opcional)
  e depois só o CNAE, repetindo até digitar "sair". O modo direto
  (`python src/cli.py 8610101 ...`) continua funcionando igual, para
  scripts e lotes.
- Reformatada a saída (`resumo()` em `modelos.py`): agora vem dividida
  em blocos com título (CST/cClassTrib, NBS/cIndOp/cTribNac, cTribMun,
  Alertas) e linhas em branco entre eles, para não ficar tudo grudado.

## 2026-09-08 — Suporte a Recife, Olinda e Jaboatão dos Guararapes
- Levantada a situação real de adoção da NFS-e Nacional nos 3
  municípios (fontes: Portaria SEFIN 12/2026, notícias especializadas e
  provedores de integração fiscal, consultado em 08/09/2026):
  - Recife: aderiu ao Emissor Nacional (Portaria SEFIN 12/2026); lista
    de serviços segue o art. 102 do CTMR.
  - Olinda: mantém sistema próprio integrado ao layout nacional desde
    22/12/2025; **alerta operacional**: hoje só o campo NBS deve ser
    preenchido na seção Reforma Tributária da nota, sob risco de erro
    de validação no provedor da prefeitura.
  - Jaboatão dos Guararapes: sistema próprio, não usa o Emissor
    Nacional (só compartilha dados para consulta); nenhuma tabela
    pública de cTribMun localizada.
- Criado `data/municipios_status.csv` e `docs/MUNICIPIOS_REGIAO_METROPOLITANA.md`
  com esse levantamento e as fontes.
- Criados `data/ctribmun/recife.csv`, `olinda.csv` e
  `jaboatao-dos-guararapes.csv`, prontos para preencher.
- `cli.py` ganhou a opção `--municipio`, que mostra o alerta
  operacional do município junto com a classificação do CNAE.

## 2026-09-08 — Dados oficiais reais (cClassTrib completo + NBS parcial)
- **cClassTrib**: substituído o exemplo por dados 100% reais e verbatim,
  extraídos ao vivo do Portal da Conformidade Fácil (SVRS) em 08/09/2026
  (`https://dfe-portal.svrs.rs.gov.br/Cff/ClassificacaoTributaria`) —
  164 códigos oficiais com CST e descrição corretos.
- `regras_setor.csv` ganhou coluna `cclasstrib_sugerido` com o código
  específico confirmado (não mais só o grupo do CST), ex.: saúde =
  200029, serviços profissionais/contabilidade = 200052, educação =
  200028, transporte coletivo = 200049, financeiro = 010002.
- **NBS**: adicionados dados reais (não mais exemplo) extraídos do PDF
  oficial do Anexo I da NBS 2.0 (Portaria Conjunta RFB/SCS), capítulos
  9, 10, 13, 14 e 15 — cobre contabilidade, jurídico, financeiro,
  imobiliário e TI. Tabela ainda PARCIAL (faltam educação, saúde,
  cultura e demais capítulos — ver nota no arquivo).
- Cadastrado override real e validado para o CNAE 6920601 (contabilidade,
  CNAE principal da empresa): CST 200, cClassTrib 200052, NBS
  1.1302.21.00. cIndOp e cTribNac desse override ainda pendentes de
  confirmação.
- cIndOp e cTribNac continuam como exemplo — não foram localizados/
  confirmados nesta sessão.

## 2026-09-08 — Correção de CST e ampliação para 6 tabelas
- Corrigido `regras_setor.csv`: setores com redução percentual (saúde,
  educação, transporte coletivo, hotelaria/turismo, cultura/esporte,
  saneamento, serviços profissionais) passaram de CST 011 para **CST
  200 (alíquota reduzida)**, com base em fonte confirmando que 200 é o
  maior grupo da tabela oficial vigente (54 dos 161 códigos, base de
  22/06/2026).
- Adicionadas 4 tabelas novas ao sistema: NBS, cIndOp, cTribNac e
  cTribMun (arquivos `*_seed.csv` como exemplo estrutural + mecanismo
  de sincronização da tabela oficial via `sincronizar_tabelas.py --tipo`).
- `overrides_operacoes.csv` ganhou colunas para as 6 tabelas.
- Alerta explícito adicionado: NBS/cIndOp/cTribNac dependem da operação
  específica, não são derivados do CNAE.

## 2026-09-08 — Criação do projeto
- Estrutura inicial criada: tabela de divisões CNAE, tabela de regras por
  setor, tabela CST de referência (18 códigos confirmados via fontes
  oficiais/imprensa especializada sobre o Informe Técnico 2025.002) e
  tabela cClassTrib semente (exemplo, a ser substituída pela oficial).
- Fonte da tabela CST: Informe Técnico 2025.002 (Portal Nacional da NF-e),
  versões acompanhadas até v1.60 (julho/2026).

<!--
Modelo para novas entradas:

## AAAA-MM-DD — <título curto>
- O que mudou (tabela oficial nova versão / operação nova da empresa / CNAE novo)
- Por quê (nota técnica X, cliente Y começou a fazer Z)
- Quem revisou
-->

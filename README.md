# Classificador Tributário por CNAE — Reforma Tributária (IBS/CBS)

Sistema em Python que recebe um **CNAE** (classe ou subclasse) e devolve
uma **sugestão** de classificação tributária para a Reforma Tributária do
Consumo (LC 214/2025), cobrindo as seis tabelas envolvidas na emissão de
um documento fiscal sob a nova sistemática:

| Código | O que identifica | Derivável do CNAE? |
|---|---|---|
| **CST** | Situação tributária do IBS/CBS | Sim (sugestão por setor) |
| **cClassTrib** | Detalhe do enquadramento legal do CST | Sim (candidatos por CST) |
| **NBS** | Qual serviço está sendo prestado | Não — depende da operação |
| **cIndOp** | Característica/local da operação | Não — depende da operação |
| **cTribNac** | Serviço na NFS-e Nacional (ISS) | Não — depende da operação |
| **cTribMun** | Complemento específico do município | Não — varia por prefeitura |

> ⚠️ **NBS, cIndOp, cTribNac e cTribMun não têm relação direta e única
> com o CNAE** — eles descrevem a operação específica (o serviço
> prestado, sua característica, o município), não a atividade econômica
> da empresa. O sistema deixa isso explícito nos alertas e oferece um
> mecanismo de **override por CNAE/operação** para você cadastrar o
> valor correto assim que validar, e reaproveitar depois.

> ⚠️ **Este sistema não substitui o julgamento do profissional.** Ele
> entrega um ponto de partida organizado a partir do CNAE. A
> classificação final de cada nota fiscal depende da natureza exata da
> operação (produto/serviço específico, finalidade, cliente), por isso
> todo resultado indica se **exige revisão manual**.

## Por que este projeto existe

As tabelas oficiais de CST e cClassTrib (Informe Técnico 2025.002 do
Portal Nacional da NF-e) têm centenas de códigos e **mudam com
frequência** (a versão 1.60, por exemplo, entrou em vigor em julho/2026).
Fazer essa consulta manualmente, CNAE por CNAE, cliente por cliente, é
lento e sujeito a erro. Este sistema:

1. Mapeia cada divisão de CNAE a um **setor da reforma** (saúde,
   educação, agropecuário, serviços profissionais regulamentados, etc.);
2. Aplica a **regra de tributação típica** daquele setor (CST, % de
   redução, base legal);
3. Sugere os **cClassTrib candidatos** compatíveis com aquele CST;
4. Permite **overrides manuais** por CNAE específico, para quando a
   empresa tiver uma operação própria que foge da regra geral do setor;
5. Mantém um **changelog** de quando a tabela oficial foi sincronizada
   e de quando novas operações foram cadastradas.

## Estrutura do projeto

```
classificador-cnae-reforma/
├── data/
│   ├── cnae_divisoes.csv              # divisão CNAE (2 díg.) -> setor da reforma
│   ├── cnae_classes_excecoes.csv      # exceções por classe CNAE (5 díg.), checadas antes da divisão
│   ├── cnae_subclasses_excecoes.csv   # exceções por CNAE completo (7 díg.), checadas antes da classe
│   ├── regras_setor.csv               # setor -> CST + cClassTrib específico, % redução, base legal
│   ├── cst_ibs_cbs.csv                # tabela de referência dos CST (IBS/CBS)
│   ├── cclasstrib_oficial.csv         # 164 códigos REAIS (Portal da Conformidade Fácil - SVRS)
│   ├── cindop_oficial.csv             # 39 códigos REAIS (Tabela de Indicadores dos Locais de Operação - SVRS)
│   ├── cclasstrib_seed.csv            # exemplo antigo, mantido apenas de referência
│   ├── nbs_oficial.csv                # NBS REAL, mas parcial (capítulos 9,10,13,14,15)
│   ├── nbs_seed.csv                   # exemplo estrutural
│   ├── ctribnac_seed.csv              # exemplo — cTribNac oficial ainda não localizado
│   ├── municipios_status.csv          # situação da NFS-e Nacional em Recife/Olinda/Jaboatão
│   ├── ctribmun/                      # UM ARQUIVO POR MUNICÍPIO
│   │   ├── recife.csv
│   │   ├── olinda.csv
│   │   └── jaboatao-dos-guararapes.csv
│   ├── overrides_operacoes.csv        # regras manuais por CNAE específico, com as 6 colunas
│   └── oficial_bruto/                 # onde você salva outros arquivos baixados de portais oficiais
├── src/
│   ├── modelos.py                     # dataclasses do sistema
│   ├── classificador.py               # lógica principal de classificação
│   ├── sincronizar_tabelas.py         # importa cClassTrib/NBS/cIndOp/cTribNac a partir de arquivo baixado manualmente
│   ├── verificar_atualizacoes.py      # checa automaticamente se as tabelas oficiais mudaram (via internet)
│   └── cli.py                         # interface de linha de comando (aceita --municipio, --detalhado)
├── tests/
│   └── test_classificador.py
├── docs/
│   ├── PASSO_A_PASSO.md                        # tutorial detalhado, do zero ao GitHub
│   ├── MUNICIPIOS_REGIAO_METROPOLITANA.md      # situação de Recife/Olinda/Jaboatão
│   └── CNAES_AMBIGUOS.md                       # registro de CNAEs corrigidos/ambíguos encontrados
├── CHANGELOG.md                       # histórico de atualizações das tabelas
├── requirements.txt
└── README.md
```

## Uso rápido

**Modo interativo (o mais simples — só rodar e digitar o CNAE):**

```bash
python src/cli.py
```

O sistema pergunta o município uma vez (pode pular com Enter) e depois
fica esperando você digitar CNAEs, um de cada vez, com a saída **enxuta**
por padrão (CST, cClassTrib, redução, base legal e situação societária
quando relevante). Digite `detalhes` para ver a versão completa do
último CNAE (NBS, cIndOp, cTribNac, todos os alertas). Para sair,
digite `sair`.

Para CNAEs de **profissões intelectuais regulamentadas** (contabilidade,
engenharia, advocacia, arquitetura, administração, etc.), o sistema
pergunta automaticamente se o contribuinte é pessoa física ou jurídica
e, se PJ, se a sociedade cumpre os 5 requisitos do art. 127 da LC
214/2025 — porque disso depende o CST ser 200 (redução de 30%) ou 000
(tributação integral). Veja a seção
[Profissões intelectuais: CST 200 x CST 000](#profissões-intelectuais-cst-200-x-cst-000)
abaixo.

**Modo direto (para scripts e lotes):**

```bash
# Um CNAE
python src/cli.py 8610101

# Vários de uma vez
python src/cli.py 8610101 6920601 4711302

# Saída completa em vez da enxuta
python src/cli.py 8610101 --detalhado

# Indicando o município do prestador (mostra alertas operacionais específicos)
python src/cli.py 6920601 --municipio "Recife/PE"
python src/cli.py 8610101 --municipio "Olinda/PE"
python src/cli.py 4711302 --municipio "Jaboatão dos Guararapes/PE"

# Profissão intelectual regulamentada, pessoa jurídica que cumpre os requisitos
python src/cli.py 7112000 --tipo-contribuinte pj --atende-requisitos-pj

# Pessoa jurídica que NÃO cumpre (perde a redução, vai para CST 000)
python src/cli.py 7112000 --tipo-contribuinte pj --nao-atende-requisitos-pj

# Pessoa física
python src/cli.py 7112000 --tipo-contribuinte pf

# Academia/personal trainer (CNAE 9313-1/00) — serviço pessoal x estrutura
python src/cli.py 9313100 --tipo-contribuinte pessoal --atende-requisitos-pj
python src/cli.py 9313100 --tipo-contribuinte estrutura

# A partir de um arquivo (um CNAE por linha)
python src/cli.py --arquivo meus_cnaes.txt
```

## Profissões intelectuais: CST 200 x CST 000

Alguns CNAEs — como engenharia, contabilidade, advocacia, arquitetura,
administração e outras profissões regulamentadas por conselho — **não
têm um CST fixo**. O art. 127 da Lei Complementar nº 214/2025 dá
redução de 30% (CST 200, cClassTrib **200052**) para 18 profissões
intelectuais, mas essa redução **depende de quem presta o serviço**:

- **Pessoa física**: redução garantida, desde que o serviço prestado
  esteja vinculado à habilitação profissional (art. 127, §1º, I).
- **Pessoa jurídica**: só mantém a redução se cumprir **todos** os 5
  requisitos cumulativos do art. 127, §1º, II — falhar em qualquer um
  derruba o benefício **inteiro**, não parcialmente:
  1. Os sócios têm habilitação ligada ao objeto da sociedade, sob
     fiscalização do respectivo conselho profissional;
  2. A sociedade **não tem** sócio pessoa jurídica;
  3. A sociedade **não é sócia** de outra pessoa jurídica;
  4. A sociedade não exerce atividade diferente da habilitação dos
     sócios;
  5. O serviço da atividade-fim é prestado diretamente pelos sócios
     (auxiliares podem ajudar, mas não substituir).

Se a pessoa jurídica **não** cumprir algum requisito, o sistema já
ajusta a sugestão para **CST 000 (tributação integral, cClassTrib
000001)** em vez de manter o CST 200 por engano.

Duas exceções que vale saber:
- **Médicos** não estão nas 18 profissões do art. 127 — quando prestam
  serviço de saúde, seguem a redução de **60%** do art. 128/Anexo III
  (a mesma regra que já se aplica a `saude_reduzida` neste sistema),
  que é mais vantajosa.
- **Educação física** (inciso X do art. 127) tem regra facilitada pelo
  **§3º**: a pessoa jurídica é **dispensada dos 5 requisitos gerais**,
  bastando estar registrada e fiscalizada pelo CREF. Mas atenção: para
  o CNAE **9313-1/00** (academias, personal trainers, pilates,
  crossfit) especificamente, **fontes divergem** sobre se isso vale
  para a academia como estabelecimento ou só para o serviço pessoal do
  profissional — veja a seção abaixo.

Fonte: art. 127, §§1º a 3º da LC 214/2025
(https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm), consultado
em 08/09/2026. Sem alteração pela LC 227/2026 até essa data.

## CNAEs com ambiguidade ou correção conhecida

Numa revisão específica, encontramos correções e ambiguidades reais:

- **CNAE 7490-1/03** (agronomia): corrigido para usar a redução de 30%
  (art. 127, XI — engenheiros agrônomos), via exceção por CNAE completo
  (7 dígitos), sem afetar as demais atividades da mesma classe
  (tradução, agenciamento etc.).
- **Divisão 74** (outras atividades profissionais): corrigido — estava
  marcada inteira como profissão regulamentada, quando na verdade é
  muito heterogênea e a maioria não está no art. 127.
- **CNAE 9313-1/00** (academia, personal trainer, pilates, crossfit):
  **ambíguo**. Uma leitura do art. 127, X e §3º sugere 30% de redução;
  uma fonte independente afirma que é tributação integral (100%). Não
  encontramos uma fonte oficial que resolva o conflito. O sistema
  assume **CST 000 por padrão** e pergunta se a operação é serviço
  pessoal do profissional (aí sugere 30%) ou acesso à
  estrutura/mensalidade (mantém 000).
- **CNAE 8591-1/00** (ensino de esportes, inclui escolinhas de
  natação): também **ambíguo**, entre a regra de educação (60%) e a de
  educação física (30%). Não achamos fonte que resolva isso com
  certeza. O sistema mostra os dois cClassTrib possíveis com alerta.

Veja a lista completa, com fontes e o raciocínio de cada caso, em
[`docs/CNAES_AMBIGUOS.md`](docs/CNAES_AMBIGUOS.md) — e adicione novos
casos lá conforme forem aparecendo. **Isso não é uma revisão exaustiva
de todos os +1.300 CNAEs existentes** — é o que conseguimos confirmar
até agora; trate como um documento vivo.

## Verificação automática de mudanças nas tabelas oficiais

Além do fluxo manual (`sincronizar_tabelas.py`, que espera um arquivo
baixado por você), o sistema tem um script que **checa sozinho, pela
internet**, se as tabelas de cClassTrib e cIndOp mudaram desde a última
vez:

```bash
pip install requests --break-system-packages   # só na primeira vez

python src/verificar_atualizacoes.py                    # checa as duas tabelas
python src/verificar_atualizacoes.py --tipo cclasstrib   # só uma
python src/verificar_atualizacoes.py --aplicar           # baixa e SUBSTITUI o CSV local
```

Por padrão ele só avisa o que mudou (códigos novos, removidos ou com
descrição diferente) — não sobrescreve nada sozinho, porque se o
layout da página do governo mudar, uma leitura errada poderia
sobrescrever dados corretos. Use `--aplicar` conscientemente e sempre
revise o resultado antes de usar em produção.

> ⚠️ Este script **não pôde ser testado de ponta a ponta** durante a
> criação deste projeto, porque o ambiente onde foi criado não tem
> acesso à internet para sites do governo brasileiro. A lógica de
> download e de extração dos dados foi escrita com base na estrutura
> real da página (a mesma que usamos para montar `cclasstrib_oficial.csv`
> e `cindop_oficial.csv`), mas teste você mesma antes de confiar nele
> — se a extração vier vazia ou estranha, o script avisa e não altera
> nada; ajuste as funções `_extrair_*_do_html` em
> `src/verificar_atualizacoes.py` se o layout tiver mudado.

## Recife, Olinda e Jaboatão dos Guararapes

O sistema tem suporte dedicado aos três municípios da Região
Metropolitana do Recife onde a Multiassiste mais atua. Cada um está em
uma situação diferente na adoção da NFS-e Nacional — os detalhes
completos, com fontes, estão em
[`docs/MUNICIPIOS_REGIAO_METROPOLITANA.md`](docs/MUNICIPIOS_REGIAO_METROPOLITANA.md).
Resumo:

| Município | Emissor | Ponto de atenção |
|---|---|---|
| **Recife/PE** | Emissor Nacional (Portaria SEFIN 12/2026) | Lista de serviços segue o art. 102 do CTMR; alguns serviços exigem informar valores repassados a terceiros |
| **Olinda/PE** | Sistema próprio, integrado ao layout nacional | ⚠️ Hoje só o campo **NBS** deve ser preenchido na seção Reforma Tributária — preencher CST/cClassTrib/cTribMun pode gerar erro de validação |
| **Jaboatão dos Guararapes/PE** | Sistema próprio (não usa o Emissor Nacional) | Nenhuma tabela pública de cTribMun localizada — confirmar com a Prefeitura |

Usando `--municipio`, o CLI já traz esse alerta junto com a classificação.
Os arquivos `data/ctribmun/recife.csv`, `data/ctribmun/olinda.csv` e
`data/ctribmun/jaboatao-dos-guararapes.csv` já estão criados,
prontos para você preencher os códigos exatos conforme for confirmando
com cada prefeitura ou com notas já emitidas.

Exemplo de saída:

```
CNAE informado: 8610101
Divisão CNAE: 86 - Atividades de atenção à saúde humana
Setor (reforma): saude_reduzida
CST sugerido: 011
Redução/observação: 60%
Base legal de referência: LC 214/2025 - Anexo de serviços de saúde
Nível de confiança da sugestão: medio
Exige revisão manual: SIM
cClassTrib candidatos (tabela local): 011001
ALERTA: Este setor tem regra de exceção/redução na reforma: confirme o
enquadramento exato do produto/serviço antes de aplicar em nota fiscal.
```

## Mantendo o sistema atualizado

Há **dois gatilhos** para revisar a lista, como você pediu:

### 1. Quando sai uma nova Nota Técnica / Informe Técnico

1. Baixe a planilha/arquivo oficial atualizado:
   - **cClassTrib/CST**: Portal Nacional da NF-e (Documentos > Diversos)
     ou `https://dfe-portal.svrs.rs.gov.br/DFE/TabelaClassificacaoTributaria`
   - **NBS, cIndOp, cTribNac**: Portal Nacional da NFS-e, documentação
     técnica — `https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica`
   - **cTribMun**: portal/suporte da prefeitura de cada município
     (não existe fonte nacional única — ver seção específica abaixo)
2. Salve o arquivo em `data/oficial_bruto/`.
3. Rode, trocando `--tipo` conforme a tabela baixada
   (`cclasstrib`, `nbs`, `cindop` ou `ctribnac`):
   ```bash
   python src/sincronizar_tabelas.py --tipo cclasstrib --arquivo data/oficial_bruto/tabela.csv --versao-it "2025.002 v1.60"
   ```
4. O script gera/atualiza o arquivo `data/<tipo>_oficial.csv` **e** grava
   uma entrada no `CHANGELOG.md` automaticamente.
5. Rode os testes (`python tests/test_classificador.py`) e dê commit.

### 2. Quando a empresa cria uma operação nova

1. Abra `data/overrides_operacoes.csv`.
2. Adicione uma linha com o CNAE e **as seis colunas validadas** (CST,
   cClassTrib, NBS, cIndOp, cTribNac, cTribMun + município) para aquela
   operação específica.
3. O override **sempre tem prioridade** sobre a regra genérica do setor.
4. Registre a mudança no `CHANGELOG.md` (modelo já incluído no arquivo).

### 3. Sobre o cTribMun (código municipal)

Diferente das outras cinco tabelas, **não existe uma tabela nacional
única de cTribMun** — cada prefeitura publica a sua. O fluxo aqui é:

1. Baixe a tabela do município do prestador (ou do cliente) no portal
   da prefeitura ou da NFS-e Nacional daquele município.
2. Salve como `data/ctribmun/<nome-do-municipio>.csv`, seguindo o
   layout de `data/ctribmun/_modelo_paulista_pe.csv`.
3. Para uma operação específica, cadastre o código já resolvido em
   `overrides_operacoes.csv` (colunas `ctribmun` e `municipio_ctribmun`).

Veja o passo a passo completo, com comandos de Git/GitHub, em
[`docs/PASSO_A_PASSO.md`](docs/PASSO_A_PASSO.md).

## Limitações conhecidas (leia antes de usar em produção)

- **cClassTrib**: hoje a tabela `data/cclasstrib_oficial.csv` tem dados
  **reais**, extraídos ao vivo do Portal da Conformidade Fácil (SVRS) em
  08/09/2026 — 164 códigos com CST e descrição oficiais. Ainda assim,
  essa tabela muda de versão com frequência (mudou em janeiro, abril e
  julho de 2026) — antes de usar em produção, reconsulte
  `https://dfe-portal.svrs.rs.gov.br/Cff/ClassificacaoTributaria` para
  confirmar que nada foi descontinuado/alterado desde então.
- **NBS**: `data/nbs_oficial.csv` tem dados **reais**, mas **parciais**
  — cobre só os capítulos 9, 10, 13, 14 e 15 da NBS 2.0 (financeiro,
  imobiliário, jurídico/contábil, profissionais e TI), extraídos do PDF
  oficial. Os demais 21 capítulos (educação, saúde, cultura, etc.)
  ainda não foram carregados — complete a partir do PDF oficial:
  `https://www.gov.br/mdic/pt-br/images/REPOSITORIO/scs/decos/NBS/`
- **cIndOp**: `data/cindop_oficial.csv` tem dados **reais e completos**
  (39 códigos), extraídos ao vivo da Tabela de Indicadores dos Locais
  de Operação do Portal da Conformidade Fácil (SVRS) em 08/09/2026.
- **cTribNac**: ainda é apenas EXEMPLO — não foi localizado/confirmado
  nesta sessão. Importe a tabela oficial da documentação técnica da
  NFS-e Nacional antes de usar em produção.
- A tabela `cnae_divisoes.csv` mapeia **divisões** (2 dígitos) a setores
  da reforma com base na estrutura pública da LC 214/2025 conhecida até
  a criação deste projeto. **Isso precisa ser validado** contra o texto
  vigente da lei e seus anexos, pois a regulamentação está sendo
  complementada por leis complementares posteriores (ex.: LC 227/2026).
- **NBS, cIndOp e cTribNac não são sugeridos a partir do CNAE** — eles
  descrevem o serviço/operação específica, não a atividade econômica da
  empresa. Ficam vazios até serem preenchidos por override ou consulta
  manual à tabela oficial (exceto onde já cadastrado em
  `overrides_operacoes.csv`, como no CNAE de contabilidade da empresa).
- **cTribMun não tem tabela nacional** — é publicada por cada
  prefeitura separadamente (ver seção "Sobre o cTribMun" acima).
- Muitos setores (agropecuário, saúde, cesta básica) dependem do
  **produto/serviço específico**, não só do CNAE — quando a regra do
  setor aponta mais de um cClassTrib possível (ex.: "200004 ou 200009
  ou 200030"), o sistema alerta que é preciso escolher o exato.
- Estas tabelas mudam de versão com frequência. **Nenhum sistema
  alimentado por memória de IA deve ser tratado como fonte oficial** —
  mesmo os dados reais aqui carregados têm uma data de consulta
  (08/09/2026) e podem ficar desatualizados. Mantenha o hábito de
  sincronizar quando sair uma nova versão.

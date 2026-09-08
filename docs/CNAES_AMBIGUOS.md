# CNAEs com ambiguidade ou correção na classificação tributária

Levantamento feito em 08/09/2026. Esta lista **não é exaustiva** — o
CNAE tem mais de 1.300 subclasses e não foi possível revisar tudo com
certeza absoluta; documentamos aqui os casos que revisamos e o que
descobrimos sobre cada um. Trate isso como um registro vivo: adicione
novos casos aqui conforme forem aparecendo na prática.

## Casos corrigidos (alta confiança)

### 7490-1/03 — Serviços de agronomia e de consultoria às atividades agrícolas e pecuárias
**Antes**: a classe 7490-1 inteira (que também inclui tradução,
agenciamento de profissionais esportivos, escafandria/mergulho, entre
outras atividades bem diferentes) estava marcada como
`servicos_profissionais_reduzida`, o que era genérico demais.
**Corrigido para**: exceção específica por subclasse completa (7
dígitos) — só a 7490-1/03 mantém a redução de 30% (art. 127, XI —
engenheiros e agrônomos), com alerta pedindo para confirmar se quem
presta o serviço é engenheiro agrônomo habilitado. As demais subclasses
da mesma classe (tradução, agenciamento, etc.) voltaram para a regra
padrão (CST 000).

### Divisão 74 — Outras atividades profissionais, científicas e técnicas
**Antes**: a divisão inteira estava marcada como
`servicos_profissionais_reduzida`. É uma divisão muito heterogênea
(design, fotografia, tradução, consultoria em geral) e a maioria das
atividades **não está** na lista das 18 profissões do art. 127.
**Corrigido para**: regra padrão (CST 000) por default, com exceções
específicas por subclasse cadastradas em
`cnae_subclasses_excecoes.csv` conforme forem confirmadas (ex:
agronomia, acima).

## Casos ainda ambíguos (sem resolução encontrada)

### 9313-1/00 — Atividades de condicionamento físico (academias, personal trainers, pilates, crossfit)

**Histórico da nossa própria correção neste projeto**: inicialmente
movemos este CNAE da regra genérica de esporte/cultura (60%) para o
art. 127, X — profissionais de educação física (30%, cClassTrib
**200052**), com base no §3º do art. 127, que dispensa a pessoa
jurídica dos 5 requisitos gerais desde que fiscalizada pelo CREF.

Depois, uma fonte independente
(hopecont.com/blog/cclasstrib-cst-ibs-cbs-tabela) afirmou o oposto:
que "Academia, CrossFit, estúdio de pilates" são **tributados
integralmente**, por não constarem nas listas de regime diferenciado.

**Não encontramos uma fonte oficial que resolva o conflito
diretamente** (não localizamos a correlação NBS → cClassTrib oficial
específica para "atividades de condicionamento físico" no Anexo VIII
da NFS-e Nacional). A leitura que adotamos, que concilia as duas
fontes sem descartar nenhuma delas, é que **a resposta certa depende
da operação**, não do CNAE:

- **Serviço pessoal do profissional** (ex: personal trainer dando aula
  individual, fiscalizado pelo CREF) → provavelmente CST 200,
  cClassTrib 200052, 30% (é a hipótese que o texto do art. 127, X e
  §3º cobre mais diretamente).
- **Acesso à estrutura / aulas em grupo** (mensalidade de academia,
  uso de equipamentos) → provavelmente CST 000, tributação integral
  (é a hipótese que o artigo da Hopecont parece descrever, e que não
  se encaixa claramente numa "prestação de serviço por profissional
  intelectual").

O sistema **não escolhe sozinho**: por padrão assume CST 000 (mais
conservador) e pergunta qual é a operação antes de sugerir 30%. Se
você tiver acesso a uma fonte que resolva isso com mais certeza (uma
Solução de Consulta, por exemplo), atualize este documento e o
`regras_setor.csv`.

**Histórico legislativo encontrado** (apresentação da ACAD — associação
das academias — ao Grupo de Trabalho da Câmara dos Deputados sobre o
PLP 68/2024, junho/2024): a própria indústria de academias reclamou,
durante a discussão do projeto, que:
- A redução de 60% de "atividades desportivas" (que virou o art. 141
  na lei final) cobria só dois incisos — **educação desportiva** (NBS
  1.2205.12.00) e **gestão de clubes filiados a federações
  esportivas** — e pediu a inclusão de um "inciso III" específico para
  "atividades de condicionamento físico". **Esse pedido não foi
  atendido**: conferimos a tabela oficial real de cClassTrib (a mesma
  que usamos para popular `cclasstrib_oficial.csv`) e ela só tem
  200041 (inciso I) e 200042 (inciso II) — sem um terceiro código para
  condicionamento físico. Isso **descarta** a hipótese de que
  academias sigam a redução de 60% do art. 141.
- Sobre a redução de 30% (art. 127), a mesma apresentação (de
  junho/2024, antes da lei ser sancionada) reclamava que a exigência de
  ser "sociedade de união de profissionais" (e não "sociedade
  empresarial") deixaria a maioria das academias de fora, já que
  operam como empresas normais, não como sociedades simples de
  profissionais.
- **Isso é relevante porque o §3º do art. 127** (que dispensa
  justamente esses requisitos para "profissão do inciso X" —
  educação física — desde que a PJ seja fiscalizada por conselho
  profissional) não aparecia nessa apresentação de 2024. É plausível
  que o §3º tenha sido incluído justamente para resolver esse tipo de
  reclamação antes da sanção da lei em janeiro/2025 — o que reforçaria
  a leitura de que a redução de 30% **deveria** valer para academias
  devidamente fiscalizadas pelo CREF. Mas isso é uma inferência
  histórica, não uma confirmação direta.

**Conclusão**: continua sem uma fonte que resolva isso com 100% de
certeza, mas agora com bem mais contexto. As três hipóteses possíveis,
em ordem do que consideramos mais provável para hoje:
1. **CST 200, cClassTrib 200052 (30%)** — se a PJ estiver devidamente
   fiscalizada pelo CREF (é obrigatório por lei sanitária que toda
   academia tenha um responsável técnico registrado no CREF) — dispensa
   do §3º do art. 127.
2. **CST 000 (tributação integral)** — se a interpretação da Hopecont
   estiver certa e a atividade de condicionamento físico simplesmente
   não constar em nenhuma lista de regime diferenciado.
3. ~~CST 200, cClassTrib 200041/200042 (60%, art. 141)~~ — **descartada**
   pela ausência de um código correspondente na tabela oficial real.

O sistema continua perguntando qual é a operação antes de decidir,
assumindo CST 000 por padrão até confirmação.

### 8591-1/00 — Ensino de esportes
Escolinhas/aulas de natação, futebol, artes marciais, tênis, mergulho,
etc. — inclui explicitamente "escolinha de natação" e é o CNAE mais
provável para uma professora de natação autônoma ou uma escolinha.

**O problema**: este CNAE está na divisão 85 (Educação), que segue a
regra geral de 60% de redução (art. 129, Anexo II, cClassTrib 200028).
Mas o serviço é claramente prestado por um profissional de educação
física (regulamentado pelo CREF), que está no rol do art. 127, X (30%
de redução, cClassTrib 200052). **Não encontramos uma fonte que resolva
com certeza qual das duas regras prevalece** para este CNAE específico.

O sistema marca este CNAE como **ambíguo** (`ensino_esportes_ambiguo`)
e mostra os dois cClassTrib possíveis com alerta, em vez de escolher um
sozinho. Recomendamos:
1. Confirmar com uma consulta formal (Consulta Fiscal) ao Comitê Gestor
   do IBS ou à Receita Federal sobre o enquadramento exato; ou
2. Verificar se já existe alguma solução de consulta/jurisprudência
   administrativa publicada sobre este caso específico; ou
3. Uma vez confirmado para um cliente específico, cadastrar a decisão
   em `data/overrides_operacoes.csv` para reaproveitar.

### Divisão 70 — Atividades de sedes de empresas e consultoria em gestão
Mantida como `servicos_profissionais_reduzida` (30%, art. 127, I —
administradores), mas com confiança **média**: nem toda "consultoria em
gestão" é prestada por administrador registrado no CRA — muitos
consultores de gestão não têm essa habilitação. O sistema já pergunta
PF/PJ e os requisitos antes de confirmar o CST, mas vale reforçar: para
este CNAE específico, confirme primeiro se o prestador é de fato
administrador habilitado antes de assumir que o art. 127 se aplica.

## Como adicionar um novo caso a esta lista

Ao identificar um novo CNAE ambíguo ou mal-classificado:
1. Pesquise a base legal (LC 214/2025 e anexos, cClassTrib oficial).
2. Adicione a exceção no arquivo mais específico possível:
   - `cnae_subclasses_excecoes.csv` (7 dígitos) — melhor opção, evita
     afetar outros CNAEs da mesma classe/divisão;
   - `cnae_classes_excecoes.csv` (5 dígitos) — quando toda a classe
     segue o mesmo tratamento;
   - `cnae_divisoes.csv` (2 dígitos) — só para correções amplas.
3. Documente o caso aqui, com fonte e data da consulta.
4. Registre no `CHANGELOG.md`.

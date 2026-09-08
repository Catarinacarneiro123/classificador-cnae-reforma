# Situação da NFS-e Nacional — Recife, Olinda e Jaboatão dos Guararapes

Levantamento feito em 08/09/2026 a partir de fontes oficiais e
especializadas. **Confirme sempre a situação atual** direto com cada
prefeitura antes de emitir — isso muda com frequência em 2026.

## Recife (código IBGE 2611606)

- Aderiu ao **Emissor Nacional de NFS-e** — Portaria SEFIN nº 12, de 29
  de abril de 2026 (publicada no Diário Oficial do Município em
  30/04/2026), regulamentando a emissão após a adesão.
- A lista de serviços tributáveis continua ancorada no **art. 102 do
  Código Tributário do Município do Recife (CTMR — Lei Municipal nº
  15.563/1991)**, que segue a Lista de Serviços da LC 116/2003.
- Regras específicas da Portaria 12/2026 que valem a pena guardar:
  - Contribuintes de certos serviços (intermediação de táxi, agências
    de turismo, publicidade, bingo, salões-parceiros) são obrigados a
    informar na NFS-e os valores repassados a terceiros.
  - Quando houver dedução ou redução de base de cálculo, a
    fundamentação legal deve constar no campo "Descrição do Serviço".
  - Regime especial de emissão para: profissionais autônomos,
    sociedades simples, MEI, cooperativas e serviços notariais/registro
    (art. 236 da CF) — esse último só ficou obrigatório 90 dias após a
    publicação da portaria (~finais de julho/2026).
  - Prazo de 60 dias da emissão para cancelamento/substituição da
    NFS-e ou rejeição pelo tomador.
- **Para achar o cTribMun exato de um serviço em Recife**: consulte o
  item correspondente no art. 102 do CTMR (o arquivo anotado da
  Prefeitura, "CTM_ANOTADO.pdf", tem a lista completa com alíquotas) ou
  confirme no Portal da SEFIN / com uma nota já emitida.

## Olinda (código IBGE 2609600)

- **Mantém sistema próprio**, mas integrado ao layout/regras da NFS-e
  Nacional desde **22 de dezembro de 2025** (implantação gradual).
- Emissão continua pelo Portal do Contribuinte da Prefeitura de Olinda
  ou por integração via Web Service — não mudou para o Emissor Nacional
  do governo federal.
- Autônomos: emissão da NFS-e Nacional obrigatória desde 1º/01/2026,
  exclusivamente pela Área Restrita do Portal do Contribuinte.
- ⚠️ **Regra prática importante, confirmada por provedor de emissão**:
  atualmente, no campo da seção "Reforma Tributária" da nota, **só o
  campo Código NBS deve ser preenchido**. Preencher os demais campos
  dessa seção (CST, cClassTrib, cTribMun) pode gerar **erro de
  validação automática no Provedor da Prefeitura de Olinda**. Isso pode
  mudar conforme a prefeitura avança na integração — reconfirme antes
  de automatizar.

## Jaboatão dos Guararapes (código IBGE 2607901)

- Situação (conforme provedor de integração fiscal consultado):
  **habilitado para emissão = sim**, **ambiente nacional (consulta) =
  sim**, **Emissor Nacional (emissão) = não**.
- Na prática: o município compartilha os dados das notas com o
  ambiente nacional (para consulta unificada), mas **a emissão
  continua pelo sistema próprio/municipal**, não pelo portal
  gov.br/nfse.
- Não foi localizada nesta consulta uma tabela pública, em formato
  aberto, com os códigos de tributação municipal (cTribMun) e alíquotas
  de ISS por item de serviço — confirme diretamente no site da
  Prefeitura (https://www.jaboatao.pe.gov.br) ou com o suporte do
  sistema de NFS-e do município.

## O que isso significa para o sistema

Nenhum dos três municípios publica uma planilha única, em formato
aberto, com todos os códigos de tributação municipal (cTribMun) — isso
é comum: **não existe uma tabela federal (nem estadual) padronizada**
para esse código, cada prefeitura mantém a sua. A forma mais confiável
de preencher `data/ctribmun/<municipio>.csv` para um cliente específico
é:

1. Conferir uma NFS-e já emitida para aquele serviço naquele município
   (o código aparece no XML/PDF da nota); ou
2. Consultar diretamente o item correspondente na lista de serviços do
   Código Tributário Municipal (no caso de Recife, o CTMR, art. 102); ou
3. Contatar o suporte do sistema de NFS-e daquele município.

Uma vez confirmado, cadastre o código em
`data/ctribmun/<municipio>.csv` (arquivos já criados para os três
municípios, prontos para preencher) e, se for para um CNAE/cliente
específico, também em `data/overrides_operacoes.csv`.

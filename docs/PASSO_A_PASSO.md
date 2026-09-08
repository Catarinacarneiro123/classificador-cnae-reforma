# Passo a passo — do zero até o GitHub

Este guia assume que você tem Python instalado e uma conta no GitHub
(a mesma usada no seu projeto `simpcalc-dados`, por exemplo).

## 1. Preparar o ambiente local

```bash
# Verifique se tem Python 3.9+
python3 --version

# Crie uma pasta e entre nela (ou use a pasta já entregue)
cd classificador-cnae-reforma

# (Opcional, mas recomendado) crie um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

Este projeto não tem dependências obrigatórias (usa só a biblioteca
padrão do Python), então nem precisa instalar nada para rodar.

## 2. Testar localmente antes de subir pro GitHub

```bash
# Modo interativo — o mais simples, só digitar o CNAE
python src/cli.py

# Ou modo direto, se preferir passar o CNAE junto do comando
python src/cli.py 8610101

# Rodar os testes automatizados
python tests/test_classificador.py
```

Se aparecer "Todos os testes passaram." e as classificações fizerem
sentido, está pronto para versionar.

## 3. Revisar e ajustar as tabelas antes do primeiro commit

Antes de publicar, vale a pena:

1. Abrir `data/cnae_divisoes.csv` e conferir se os setores fazem sentido
   para os **CNAEs dos seus clientes** — você conhece a carteira melhor
   que qualquer tabela genérica.
2. Abrir `data/regras_setor.csv` e ajustar percentuais/base legal
   conforme a regulamentação for avançando.
3. Se já tiver casos concretos de operações específicas, cadastrar em
   `data/overrides_operacoes.csv`.

## 4. Criar o repositório no GitHub

Você pode criar direto pelo site ou pelo terminal (com `gh`, se tiver o
GitHub CLI instalado). Pelo site é mais simples:

1. Acesse https://github.com/new
2. Nome sugerido: `classificador-cnae-reforma`
3. Descrição sugerida: "Classificador tributário (CST/cClassTrib) por
   CNAE para a Reforma Tributária — projeto de estudo/portfólio"
4. Marque como **público** (bom para portfólio) ou privado, como preferir
5. **Não** marque para criar README/gitignore automaticamente (você já
   tem os seus) — ou, se marcar, vai precisar resolver conflito no passo 6.
6. Clique em "Create repository"

## 5. Inicializar o Git localmente

Dentro da pasta `classificador-cnae-reforma`:

```bash
git init
git add .
git commit -m "Primeira versão: classificador tributário por CNAE"
```

## 6. Conectar ao repositório remoto e enviar

O GitHub mostra a URL do seu repositório depois de criado. Vai ser algo
como:

```bash
git remote add origin https://github.com/Catarinacarneiro123/classificador-cnae-reforma.git
git branch -M main
git push -u origin main
```

Se pedir autenticação, use um **token de acesso pessoal** (o GitHub não
aceita mais senha comum para push via HTTPS) — em
Settings > Developer settings > Personal access tokens.

## 7. Confirmar que subiu certo

Atualize a página do repositório no navegador e confira se aparecem:
- README.md renderizado na página inicial
- As pastas `data/`, `src/`, `tests/`, `docs/`

## 8. Fluxo de manutenção (o "revisar quando mudar")

**Se você prefere não digitar comandos de Git**, veja
[`docs/GUIA_GIT_SIMPLES.md`](docs/GUIA_GIT_SIMPLES.md) — tem um
arquivo (`atualizar-github.bat`) que faz tudo com um duplo-clique, e
também a opção de usar o GitHub Desktop (programa com botões).

Sempre que:

- **sair uma nova Nota Técnica/Informe Técnico** alterando cClassTrib ou
  CST → rode `src/sincronizar_tabelas.py` (veja instruções no próprio
  arquivo e no README) e depois:
  ```bash
  git add data/cclasstrib_oficial.csv CHANGELOG.md
  git commit -m "Atualiza tabela cClassTrib para IT 2025.002 vX.XX"
  git push
  ```

- **a empresa criar uma operação nova** → edite
  `data/overrides_operacoes.csv`, adicione uma linha no `CHANGELOG.md`
  explicando a operação, e:
  ```bash
  git add data/overrides_operacoes.csv CHANGELOG.md
  git commit -m "Adiciona override para nova operação: <descrição curta>"
  git push
  ```

## 9. Ideias para evoluir o projeto (opcional, quando tiver tempo)

- Trocar o CLI por uma telinha web simples com **Streamlit**
  (`pip install streamlit`), reaproveitando `ClassificadorTributarioCnae`
  sem mudar a lógica.
- Ler uma planilha de clientes (Excel/CSV) com uma coluna de CNAE e gerar
  automaticamente uma coluna de CST/cClassTrib sugerido para todos de
  uma vez (dá pra fazer com `csv` puro ou com `pandas`).
- Criar um GitHub Action que roda os testes automaticamente a cada push
  (arquivo `.github/workflows/testes.yml`) — bom item de portfólio para
  mostrar prática de CI/CD.
- Adicionar um campo de "data da última revisão" por linha do
  `regras_setor.csv`, para saber rapidamente o que está desatualizado.

## 10. O que NÃO automatizar

Evite deixar o sistema "decidir sozinho" e emitir a nota fiscal com o
CST/cClassTrib sugerido sem revisão, especialmente nos setores marcados
com `exige_revisao_manual = sim`. A ideia aqui é **acelerar a consulta**,
não substituir a análise fiscal — principalmente enquanto a
regulamentação da reforma ainda está sendo complementada por novas leis
complementares e notas técnicas.

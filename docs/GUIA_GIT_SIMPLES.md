# Guia rápido: atualizando o projeto sem decorar comandos

Você não precisa saber Git de verdade pra manter esse projeto. Este
guia mostra o caminho mais simples.

## Opção 1 (mais fácil): o arquivo `atualizar-github.bat`

Toda vez que eu (ou você) mudar algo no sistema:

1. Extraia os arquivos novos por cima da pasta do projeto
2. Dê **dois cliques** no arquivo `atualizar-github.bat` (está na raiz
   da pasta, junto com o README.md)
3. Uma janela preta vai abrir e perguntar: **"Descreva em poucas
   palavras o que você mudou"** — digite algo curto, tipo `Corrige CST
   da academia` ou `Adiciona novo cliente`, e aperte Enter
4. Espera terminar (aparece "Pronto!" no final) e fecha a janela

Pronto — isso já faz tudo: salva as mudanças e envia pro GitHub. Não
precisa digitar `git add`, `git commit` nem `git push` nunca mais.

## Opção 2: GitHub Desktop (programa com botões, sem terminal)

Se quiser algo ainda mais visual — com uma tela normal de programa, em
vez de uma janela preta de comandos — existe um aplicativo oficial do
GitHub chamado **GitHub Desktop**:

**https://desktop.github.com/**

Depois de instalar e logar com sua conta, ele mostra:
- Uma lista dos arquivos que mudaram (igual um "o que foi editado no Word")
- Uma caixinha pra escrever o que você mudou
- Um botão azul escrito **"Commit to main"**
- Um botão **"Push origin"** pra enviar

É o mesmo processo do `atualizar-github.bat`, só que com uma interface
gráfica em vez de linha de comando. Escolha o que for mais confortável
pra você — os dois fazem a mesma coisa.

## O que fazer se aparecer um erro

Se o `.bat` ou o GitHub Desktop mostrarem algum erro estranho, tira um
print e pergunta pro Claude (ou pra mim, se for outro dia) — não tem
problema em pedir ajuda de novo, isso é normal em qualquer fluxo de
trabalho com Git, até para quem usa há anos.

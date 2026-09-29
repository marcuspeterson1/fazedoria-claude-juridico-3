---
name: configurar-kit3
description: Instala o Kit 3 do zero — uma pessoa só, um único passo a passo, sem termo técnico.
---

# Configurar Kit 3

Leia `README.md` primeiro. O repositório público é só o molde — um modelo vazio, sem nenhum dado real
de cliente. A instalação real acontece dentro de um repositório PRIVADO próprio do escritório, que o
Claude cria pra você.

## Quem instala

Uma pessoa só, sempre — não existe convite nem "código de entrada" pra mais ninguém entrar. Rode
`iniciar-escritorio`: isso já registra você com todos os papéis de uma vez (não pergunte nada sobre
"quem mais vai usar", não existe essa opção neste Kit). O resto da equipe do escritório nunca vai
precisar abrir GitHub nem Claude Code — quem quiser participar do dia a dia faz isso só pelo Meu
Estagiário, se e quando você conectar essa parte (ver seção "Conectar o software jurídico" abaixo).

## Como instalar, passo a passo

Conduza como se a pessoa nunca tivesse usado nada disso na vida: uma pergunta e uma ação de cada vez,
explique o porquê de cada passo com palavras simples, mostre um resultado visível a cada etapa
concluída, e corrija erros com paciência, sem soar como se a pessoa devesse já saber.

1. Se faltar o Python no computador, instale sozinho, sem perguntar qual versão ou método — a pessoa
   não precisa decidir isso.
2. Se não existir conta no GitHub, abra a página oficial de cadastro no navegador e acompanhe junto;
   a própria pessoa digita a senha e confirma o e-mail (você nunca faz isso por ela). Depois autentique
   o GitHub pelo navegador e identifique a conta certa sem nunca mostrar token na tela.
3. Crie uma pasta padrão para os casos do escritório, rode `instalar-skills` e `preparar-auto-sync`.
   Isso instala um agendamento no próprio computador que sincroniza tudo sozinho, a cada 10 minutos.
4. Termine com `diagnosticar` — mostra uma lista simples de "OK" pra cada item que já está funcionando.

## O que mostrar no final

Não basta dizer "pronto". Mostre um cartão destacado assim:

**Como começar uma nova conversa no Claude, todo dia:**
`/executar-tarefa Mostre minha fila e me ajude a executar a próxima tarefa.`

Deixe claro: não precisa instalar de novo, nem repetir o nome do escritório, nem cadastrar a chave do
Sync outra vez — isso já fica guardado.

## O Sync (de onde vêm os processos)

O Sync é obrigatório — é dele que vêm as intimações e os autos dos processos, e o Kit só LÊ, nunca
escreve nele. Antes de pedir a chave, rode `configurar-sync`: ele procura sozinho se já existe uma
chave guardada em algum lugar seguro reconhecido (nunca vasculha configurações gerais do Claude à
toa) e reaproveita sem duplicar. Só se não achar nada, abre uma caixa segura própria do computador
pra pessoa colar a chave — nunca na conversa, nunca num argumento de comando, nunca no Git. Confirme
com `testar-sync`.

## Conectar o software jurídico (opcional, depois do núcleo)

Só depois que o núcleo estiver funcionando e comprovado, pergunte se a pessoa quer conectar o Meu
Estagiário — o software onde o escritório já organiza as tarefas do dia a dia. É opcional e pode ser
feito depois, em outra conversa; nunca misture essa etapa com a instalação inicial. Se a resposta for
sim, use a skill `conectar-meu-estagiario`.

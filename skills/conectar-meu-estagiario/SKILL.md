---
name: conectar-meu-estagiario
description: Liga o Kit 3 ao Meu Estagiário do escritório, passo a passo, para quem nunca configurou nada técnico.
---

# Conectar o Meu Estagiário

Isso é uma etapa opcional, só depois que o núcleo do Kit já estiver instalado e funcionando. Explique
com uma frase simples antes de começar: "o Sync continua sendo de onde vêm os processos e as
intimações; o Meu Estagiário vai virar o lugar onde você acompanha e responde as tarefas — sem
precisar abrir o Claude toda hora."

Antes de agir, confira se o Kit já está instalado num repositório privado do escritório. Leia
integralmente `integracoes/meu-estagiario/README.md`, `integracoes/meu-estagiario/pacote/LEIA-ME.md`
e `integracoes/meu-estagiario/pacote/INSTRUCOES_AGENTE.md` antes de tocar em qualquer arquivo.

## Passo a passo

1. Peça a chave do Meu Estagiário (formato `mea_...`) por uma caixa segura do computador — nunca
   peça para colar aqui na conversa.
2. Rode o instalador do pacote (`integracoes/meu-estagiario/pacote/instalar.py`). Ele confere se a
   chave funciona, lê o cadastro real do escritório (pessoas, tipos de tarefa, etapas de caso) e
   guarda só o NOME da variável — nunca a chave em si — na configuração local.
3. Rode o teste opcional (`--test-write`): ele cria uma tarefa claramente marcada como teste,
   confirma que ela mudou de status de verdade (não confia só em "deu certo"), escreve uma nota
   avisando que é teste, e arquiva no final. Nenhum caso real é tocado.
4. Só depois disso, pergunte se a pessoa quer o **motor** — a parte que faz o ciclo rodar sozinho,
   sem ninguém abrir o Claude todo dia. Explique em uma frase: "uma nota sua no card dispara a
   esteira a produzir a minuta sozinha, e o link volta pronto pra você revisar." Instale e agende o
   motor como passo SEPARADO, nunca junto com o resto — a pessoa precisa decidir isso conscientemente.

## Regras de segurança

Nunca peça ou grave a chave na conversa ou no Git — sempre pela caixa segura do próprio computador.
Só declare a etapa concluída depois do teste passar, com leitura de volta confirmando (nunca confie
num "HTTP 200" sozinho) e o arquivo `resultado_instalacao.json` aprovado. O Sync continua só leitura.
O protocolo do processo continua manual, sempre — o Kit nunca protocola nada sozinho.

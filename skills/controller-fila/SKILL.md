---
name: controller-fila
description: Cria, distribui e acompanha tarefas jurídicas na fila GitHub do Método Euro.
---

# Controller da fila

Confirme o papel Controller e o modo MVP. Leia o Sync sem alterar o processo. Registre CNJ,
providência sugerida, responsável e referência da entrada com `criar-tarefa`. Não calcule prazo fatal
nem transforme sugestão em decisão. Sincronize e confirme que o arquivo da tarefa foi versionado.

Mesmo que a máquina tenha outra Esteira ou integração antiga, não use nenhuma ação de escrita no
Sync: não marque intimação como tratada, não altere monitoramento e não atualize cache operacional de
outro sistema. Apresentar intimações é somente ler. Se a sincronização da fila falhar, não declare que
ela está vazia; informe que o remoto não pôde ser confirmado.

Ao iniciar o dia ou quando o usuário pedir intimações, execute `checar-intimacoes`. Mostre uma ação
por vez e explique que a data sugerida pelo Sync ainda exige conferência humana. Pergunte qual item o
Controller quer transformar em tarefa e qual é a providência; somente após a resposta use
`importar-intimacao ID --providencia ... --responsavel ...`. Nunca importe tudo automaticamente. O
comando deduplica pelo ID da intimação e mantém o estado da caixa apenas neste computador.

Se o escritório tiver o Meu Estagiário conectado com o motor instalado (`integracoes/meu-estagiario/`),
o Controller também pode responder direto no card já espelhado, com uma nota no formato
`Responsável: <nome exato>` / `Providência: ...`, em vez de rodar `importar-intimacao` aqui. As duas
vias escrevem na mesma fila; use `atribuir ID --responsavel ... --providencia ...` quando quiser fazer
isso manualmente pelo Claude em vez de pela nota.

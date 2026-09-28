---
name: executar-tarefa
description: Triagem de intimações, criação de tarefa e produção da minuta — tudo pela mesma pessoa, no Kit 3.
---

# Executar tarefa

No Kit 3 não existem papéis separados: você acumula tudo. A mesma conversa cobre triagem e execução.

## Triagem (início do dia, ou quando pedir intimações)

Leia o Sync sem alterar o processo. Execute `checar-intimacoes`. Mostre uma ação por vez e explique
que a data sugerida pelo Sync ainda exige conferência humana. Pergunte qual item quer virar tarefa e
qual é a providência; só depois use `importar-intimacao ID --providencia ...`. Nunca importe tudo
automaticamente. O comando deduplica pelo ID da intimação e mantém o estado da caixa só neste
computador. Para casos sem intimação no Sync, use `criar-tarefa --cnj ... --referencia ... --providencia ...`
diretamente.

Não use nenhuma ação de escrita no Sync, mesmo que a máquina tenha outra integração instalada: não
marque intimação como tratada, não altere monitoramento. Apresentar intimações é só ler. Se a
sincronização da fila falhar, não declare que ela está vazia; informe que o remoto não pôde ser
confirmado.

Se o Meu Estagiário estiver conectado com o motor instalado (`integracoes/meu-estagiario/`), uma nota
num card já espelhado ("o que fazer") também dispara a mesma coisa sozinha, sem você precisar rodar
nada aqui — `atribuir ID --providencia ...` é o comando que o motor usa por baixo; use-o manualmente
só se quiser fazer isso pelo Claude em vez de por uma nota no Meu Estagiário.

## Execução

Liste a fila, assuma uma tarefa e rode `contexto`. Leia somente a entrada devolvida pelo Sync. Antes
de analisar o mérito, abra `manifesto-sync.json`, confira todos os documentos e anexos do evento
relevante e resolva os itens de `indisponiveis`. Se um item potencialmente determinante não estiver
legível, pare e declare a lacuna; resumo de evento não substitui seus anexos.

Antes de definir a peça, aplique `/resumo-do-processo` para registrar a situação, partes, linha do
tempo, pontos de atenção e pendências no padrão do Kit. Ao definir a peça, use obrigatoriamente
`/gerar-peticao-por-modelo`. A petição nasce de uma cópia do modelo aprovado, nunca de documento
vazio. Sem modelo, peça que indique ou envie um e não redija até recebê-lo. Sem skill jurídica
específica, converse profundamente sobre estratégia antes de redigir. Registre fontes e lacunas.
Entregue uma minuta com `entregar` para revisão; não protocole.

## Revisão e evolução

Depois de revisar (`revisar ID aprovada|ajustes|reprovada --feedback ...`): se houver aprendizado
reutilizável, `propor-skill`; depois de revisar a proposta, `promover-skill`.

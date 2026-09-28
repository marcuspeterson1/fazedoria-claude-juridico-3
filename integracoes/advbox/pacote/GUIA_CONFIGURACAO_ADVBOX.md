# Guia do agente — instalar a Esteira dentro da ADVBOX

Este é um instalador híbrido. A API audita e opera tarefas; tipos de tarefa e Flowter são criados
pela interface porque essas mutações não estão expostas na API pública documentada.

## Checkpoint 1 — pré-requisitos

- O aluno continuará usando a ADVBOX como fila operacional.
- Um usuário com perfil **Gestor** acompanha a configuração; apenas Gestores criam tipos de tarefa.
- O plano precisa oferecer Workflow ou Flowter. Se não oferecer, use o modo prévio por API/polling.
- A chave da API fica em secret store local, nunca no chat ou no Git.

## Checkpoint 2 — tipos de tarefa

Abra `Configurações → Tarefas`. Crie somente os nomes ausentes listados pelo instalador, exatamente
como aparecem em `manifesto.json`. Não edite, inative ou substitua tarefas preexistentes. Para cada
tipo, pergunte ao Dono a fase aplicável, complexidade, tempo médio e Taskscore; não invente pontos.

Rode novamente `instalar.py --verify-only`. O resultado deve apresentar os oito IDs, sem ausências.

## Checkpoint 3 — Flowter ou Workflow

No Flowter, crie três fluxos conforme o manifesto:

1. `Método Euro - Produção e revisão`: validar entrada → produzir minuta → revisar minuta.
2. `Método Euro - Refação`: refazer minuta → revisar minuta.
3. `Método Euro - Protocolo manual`: aprovada → protocolar manualmente → confirmar protocolo.

Na versão Workflow, monte as mesmas sequências em `Configurações → Workflow`. Defina responsáveis e
prazos com o Dono, uma pergunta por vez. Não marque automaticamente protocolo como concluído.

Registre uma captura da configuração final e passe seu caminho em `--evidencia-interface`. O hash da
imagem entra no resultado local; a imagem não entra no Git.

## Checkpoint 4 — teste controlado

Escolha com o Dono um processo/caso autorizado para teste e um usuário responsável. Execute o teste
com os dois IDs. O instalador cria `[EURO] VALIDAR ENTRADA`, relê por ID e deixa a conclusão manual.
Não use prazo fatal, não anexe documento real e não exclua tarefa para “limpar” o teste.

## Como o Claude opera depois

`ponte.py` cria na própria ADVBOX a próxima tarefa, primeiro em simulação e depois com `--confirmar`.
Um marcador impede duplicação. O Claude/worker lê a tarefa de produção, busca os autos no Sync,
trabalha sobre cópia do modelo aprovado e cria a tarefa de revisão na ADVBOX com o link da minuta.
O revisor humano decide: refação ou aprovação. O protocolo e sua confirmação permanecem manuais.

O pacote ainda não instala um worker contínuo. Para automação permanente, há duas rotas posteriores:

- polling seguro da API `/posts` por um serviço local/VPS; ou
- Flowter enviando HTTP Request para um webhook do n8n/worker.

Só chame uma dessas rotas de implantada depois de configurar o runtime, testar ponta a ponta e
observar uma execução real.

## Fontes oficiais conferidas

- Tipos de tarefa e permissão de Gestor: https://guia.advbox.com.br/menu-configuracoes/tarefas-e-taskscore
- Flowter, gatilhos e HTTP Request: https://guia.advbox.com.br/flowter/funcoes-flowter
- Workflow e sequências: https://guia.advbox.com.br/menu-configuracoes/workflow
- API e nodes para n8n: https://guia.advbox.com.br/api/integracao-advbox-n8n
- Geração e proteção do token: https://guia.advbox.com.br/api/api-token-entenda-melhor

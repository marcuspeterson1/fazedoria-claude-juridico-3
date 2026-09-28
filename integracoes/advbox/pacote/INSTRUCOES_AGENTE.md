# Instruções obrigatórias para o agente

1. Assuma que o aluno continuará na ADVBOX; não proponha migração para outro software.
2. Leia `manifesto.json`, `GUIA_CONFIGURACAO_ADVBOX.md`, `CONTRATO_DO_WORKER.md`, `instalar.py` e
   `ponte.py` integralmente.
3. Receba o token por entrada segura local e nunca o grave na conversa ou no Git.
4. Rode primeiro o instalador em verificação. Se retornar código 20, abra a ADVBOX autenticada e
   crie somente o que estiver ausente, com um Gestor, uma pergunta por vez.
5. Não altere tipos de tarefa ou workflows já existentes. Repetir a instalação não pode duplicar.
6. Escolha pontos, responsáveis e prazos com o Dono; não invente regras do escritório.
7. Faça a captura de evidência e rode novamente o instalador.
8. O teste real exige caso e usuário expressamente escolhidos; a tarefa de teste é relida e fica para
   conclusão humana. Nunca teste com prazo fatal.
9. Não mexa em clientes, processos, movimentações ou financeiro. A escrita autorizada por este pacote
   limita-se a criar tarefas da Esteira em `/posts`.
10. Diferencie estrutura configurada, conexão API, tarefa de teste, worker implantado e execução
    ponta a ponta. Não declare automação contínua antes de ela existir.

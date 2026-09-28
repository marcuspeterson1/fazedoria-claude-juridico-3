# Instruções para o agente instalador

1. Confirme que o destino é o clone privado do escritório e que o núcleo do Kit já está instalado.
2. Obtenha a chave por caixa segura ou secret store. Nunca peça que seja colada na conversa.
3. Rode os testes locais e depois `instalar.py --kit-root ... --test-write`.
4. O teste deve usar somente tarefa sintética e ser arquivado; nunca use caso ou cliente real.
5. Confira o arquivo de resultado. HTTP 200 sem leitura de volta não é prova.
6. Não escreva em financeiro, não altere skills do Meu Estagiário e não use `/chat`.
7. O Sync permanece somente leitura. Aprovação jurídica e protocolo manual são gates distintos.
8. `ponte.py` sozinho espelha só uma tarefa por chamada. Se o usuário quiser o ciclo fechando
   sozinho (Controller responde por nota, motor atribui e dispara a minuta headless), ofereça o
   motor (`motor.py`) como passo SEPARADO e explícito — nunca instale silenciosamente.
9. Antes de instalar o agendamento do motor, confirme: a variável `MEU_ESTAGIARIO_API_KEY` precisa
   estar disponível de forma PERMANENTE no ambiente da máquina (não só na sessão atual), porque o
   agendamento roda sem terminal e sem humano pra digitar a chave. Rode
   `python3 motor.py ciclo --kit-root ...` manualmente pelo menos uma vez, mostre o resultado ao
   usuário e só then ofereça `instalar-agendamento`.
10. O motor só atribui responsável quando o nome na nota bate EXATAMENTE (sem acento/maiúscula
    importar) com um nome em `/membros`. Isso não basta sozinho: o texto gravado na fila do Kit
    também precisa bater exatamente com o nome que aquele colaborador usou ao entrar no Kit
    (Prompt 2, "--nome"). Avise o usuário: mais seguro usar o MESMO nome nos dois lugares.
11. O motor NUNCA escolhe skill jurídica específica por conta própria além do que o próprio
    escritório já tiver criado (Ato 2) — sem isso, cai no genérico `gerar-peticao-por-modelo`.
    Não prometa que o motor "sabe" qual petição escrever; ele repete o método, não substitui a
    criação da skill.
12. Se a minuta não sair sozinha num ciclo, o motor deixa uma nota pedindo continuação humana e
    NÃO tenta de novo sozinho na tarefa seguinte (evita ficar rodando o mesmo caso indefinidamente
    sem revisão) — quem retoma é um humano abrindo conversa normal no Claude.

Informe ao usuário: conta validada, catálogos lidos, teste sintético, caminho da configuração local
e se houve vínculo exato de caso e responsável. Nunca mostre a chave.

# Instruções para o agente instalador

1. Confirme que o destino é o clone privado do escritório e que o núcleo do Kit já está instalado.
2. Obtenha a chave por caixa segura ou secret store. Nunca peça que seja colada na conversa.
3. Rode os testes locais e depois `instalar.py --kit-root ... --test-write`.
4. O teste deve usar somente tarefa sintética e ser arquivado; nunca use caso ou cliente real.
5. Confira o arquivo de resultado. HTTP 200 sem leitura de volta não é prova.
6. Não escreva em financeiro, não altere skills do Meu Estagiário e não use `/chat`.
7. O Sync permanece somente leitura. Aprovação jurídica e protocolo manual são gates distintos.
8. `ponte.py` sozinho espelha só uma tarefa por chamada. Se o usuário quiser o ciclo fechando
   sozinho (uma nota no card já espelhado dispara o motor, que registra a providência e produz a
   minuta na mesma passada), ofereça o motor (`motor.py`) como passo SEPARADO e explícito — nunca
   instale silenciosamente.
9. Antes de instalar o agendamento do motor, confirme: a variável `MEU_ESTAGIARIO_API_KEY` precisa
   estar disponível de forma PERMANENTE no ambiente da máquina (não só na sessão atual), porque o
   agendamento roda sem terminal e sem humano pra digitar a chave. Rode
   `python3 motor.py ciclo --kit-root ...` manualmente pelo menos uma vez, mostre o resultado ao
   usuário e só então ofereça `instalar-agendamento`.
10. Kit 3 é operado por uma pessoa só (o Dono acumula todos os papéis) — não existe "atribuir a
    outra pessoa". O motor não tenta casar nome nenhum: qualquer nota nova (que não seja dele
    mesmo) já vira a providência da tarefa, atribuída ao próprio Dono, e o motor tenta produzir a
    minuta na mesma passada.
13. Cada ciclo do motor também roda a CAPTAÇÃO primeiro: qualquer intimação pendente já em cache
    local (`.intimacoes-inbox/intimacoes.json`, atualizado 1x/dia pelo auto-sync do núcleo) vira
    tarefa e card no Meu Estagiário sozinha, sem decisão humana prévia — a decisão continua
    existindo, só que dentro do Meu Estagiário, pela nota. Isso é o que fecha o ciclo diário sem
    o usuário precisar abrir o Claude nenhuma vez.
11. O motor NUNCA escolhe skill jurídica específica por conta própria além do que o próprio
    escritório já tiver criado (Ato 2) — sem isso, cai no genérico `gerar-peticao-por-modelo`.
    Não prometa que o motor "sabe" qual petição escrever; ele repete o método, não substitui a
    criação da skill.
12. Se a minuta não sair sozinha num ciclo, o motor deixa uma nota pedindo continuação humana e
    NÃO tenta de novo sozinho na tarefa seguinte (evita ficar rodando o mesmo caso indefinidamente
    sem revisão) — quem retoma é um humano abrindo conversa normal no Claude.

Informe ao usuário: conta validada, catálogos lidos, teste sintético, caminho da configuração local
e se houve vínculo exato de caso e responsável. Nunca mostre a chave.

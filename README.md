# Kit 3 - Ligando o Motor da sua Esteira

Versão 3.0.0. Kit 3 é operado por **uma pessoa só** — você, o Dono, acumulando todos os papéis num
único Claude Code. Não existe convite, código de colaborador nem clone de segunda pessoa: o resto da
sua equipe só interage pelo Meu Estagiário (ou outro software jurídico que você já usa), nunca com
GitHub ou Claude Code. É assim que uma esteira de petições real começa a funcionar.

O repositório público deste Kit é apenas o molde, sem dados. Durante a instalação, o Claude cria um
novo repositório **privado** para o seu escritório — a fonte canônica do que você faz, sob sua própria
conta do GitHub. O núcleo funciona sem software jurídico nenhum:

`Sync (autos, leitura) → sua fila → você produz → você revisa → proposta → skill`

O Sync é obrigatório como fonte de autos. Infinitum, Meu Estagiário e Advbox são conectores opcionais,
instalados só depois de você comprovar o núcleo funcionando. O modo inicial é `mvp`: trabalha com
tarefas reais e permite leitura dos autos no Sync, mas mantém bloqueada qualquer escrita em sistemas
externos.

Com o Meu Estagiário conectado, um **motor opcional** (instalado à parte, nunca junto do núcleo) fecha
o ciclo sozinho: você escreve uma nota num card já espelhado dizendo o que fazer, e o motor registra a
providência, dispara headless a mesma skill de produção que você rodaria, e devolve o link da minuta
como nota na mesma tarefa. Revisão humana e protocolo manual continuam separados, sempre.

📄 **[Veja o dia a dia em formato visual, sem termo técnico: `POP-DIA-A-DIA.html`](POP-DIA-A-DIA.html)**
(abra em qualquer navegador) — quem faz o quê, o que roda sozinho e o que depende de você.

## Instalação guiada — um prompt só

Você envia um único prompt ao Claude Code na pasta permanente `Claude`; não precisa abrir Terminal ou
PowerShell.

```text
Instale o Kit 3 - Ligando o Motor da sua Esteira usando esta fonte oficial:
https://github.com/marcuspeterson1/fazedoria-claude-juridico-3

Leia e audite os arquivos desse repositório antes de executar qualquer coisa. Faça tudo por mim
usando suas ferramentas internas, sem me mandar abrir terminal. Instale silenciosamente os
pré-requisitos oficiais e seguros que faltarem, inclusive Python 3, sem me pedir para escolher o
método. Só me interrompa para login oficial no GitHub ou decisão pessoal realmente inevitável.

Antes de instalar, verifique se este Kit já existe e está configurado neste computador. Se existir,
não recomece: use a skill `atualizar-kit`, compare a versão pública com a instalada e aplique somente
as novidades, preservando escritório, fila, entregas, skills, caminhos e credenciais.

Estou criando o escritório. Peça somente meu nome e o nome do escritório. Crie um novo repositório
privado, copie o Kit, confirme no GitHub que está privado e execute `iniciar-escritorio`. Eu acumulo
todos os papéis sozinho — não crie convite nem pergunte se outra pessoa vai usar o Claude Code aqui.

Explique que o Sync é a fonte obrigatória dos autos. Abra uma caixa segura do próprio computador para
eu cadastrar a chave do Sync sem digitá-la nesta conversa. Execute `configurar-sync` e `testar-sync`.

Configure comigo o padrão de documentos do escritório, uma pergunta por vez: onde ficam os modelos
aprovados; onde ficam as pastas dos clientes, se existirem; se a cópia do modelo deve ser salva na
pasta do cliente ou em outro lugar; e qual é o padrão de nomes dos arquivos. Registre as regras com
`configurar-documentos`, mas guarde caminhos específicos desta máquina somente na configuração local.
Explique que toda petição deve nascer de uma cópia de modelo aprovado para preservar logomarca,
timbre, cabeçalho, rodapé, formatação e tópicos jurídicos validados. Nunca altere o modelo original.
Se não houver modelo adequado, peça que eu indique ou envie um antes de redigir.

Crie automaticamente uma pasta local padrão para os casos. Instale e ative a sincronização em
segundo plano. Antes de mostrar a fila, sincronize silenciosamente; depois de assumir, entregar,
revisar ou criar uma tarefa/skill, salve e envie silenciosamente. Não ensine Git nem peça comandos.

Explique conceitos com palavras simples, uma ação por vez e checkpoints curtos. Não solicite nem
grave tokens na conversa ou no Git. Não habilite Infinitum, Meu Estagiário, Advbox nem escrita em
sistema externo nesta etapa inicial. Ao final, rode o diagnóstico e mostre apenas o que está pronto e
qualquer ação pessoal inevitável.
```

## Fluxo operacional

O computador executa `iniciar-escritorio` uma única vez. Depois:

- `python3 esteira.py instalar-skills` liga a fonte canônica aos diretórios reconhecidos por Claude Code
  e Codex, preservando qualquer instalação preexistente.
- A skill `resumo-do-processo` transforma os autos obtidos no Sync em um resumo jurídico padronizado
  antes da escolha e execução da peça.
- A skill `gerar-peticao-por-modelo` copia o modelo aprovado, preserva a identidade visual e mantém
  apenas os tópicos jurídicos aplicáveis, com registro do modelo e do destino da cópia.
- `python3 esteira.py preparar-auto-sync` cria os arquivos locais para sincronização conservadora a cada
  dez minutos e consulta, no máximo uma vez por dia, a caixa de intimações no Sync. O Claude
  instala/ativa o agendamento nativo do sistema e comprova uma execução.

1. Triagem: `checar-intimacoes`; escolhe um item e confirma a providência com `importar-intimacao`, ou
   cria diretamente com `criar-tarefa`.
2. Execução: `listar`, `assumir ID`, `contexto ID`, copia o modelo aprovado, produz a peça e usa
   `entregar ID ARQUIVO --modelo IDENTIFICAÇÃO --copia-destino DESTINO`.
3. Revisão: `revisar ID aprovada|ajustes|reprovada --feedback ...`.
4. Se houver aprendizado reutilizável: `propor-skill`; depois de revisar, `promover-skill`.

A skill `executar-tarefa` cobre as quatro etapas — não são papéis diferentes, é o mesmo Claude
ajudando você em momentos diferentes do dia. Toda mutação operacional cria commit e sincroniza
automaticamente; em conflito, o Kit para e preserva o estado para conciliação, sem apagar versões.

## O que roda sozinho, e o que ainda depende de você abrir o Claude

Sem o Meu Estagiário conectado, o Kit é MVP: nada cria tarefa sozinho, e você só vê a fila abrindo o
Claude e mandando `/executar-tarefa Mostre minha fila e me ajude a executar a próxima tarefa.`.

Com o Meu Estagiário conectado e o motor agendado (`integracoes/meu-estagiario/`), o ciclo diário
roda sem você abrir o Claude:

1. A cada 10 minutos, o agendamento do núcleo sincroniza a fila e, no máximo 1x por dia, consulta
   intimações novas no Sync.
2. A cada 10 minutos, o motor pega as intimações novas e, sozinho, cria a tarefa e o card
   correspondente no Meu Estagiário — sem esperar ninguém decidir nada.
3. Você lê o card no Meu Estagiário e escreve uma nota dizendo o que fazer. Se o caso for de outra
   pessoa do seu time, a nota pode incluir `Responsável: <nome exato>` para o card passar a
   aparecer para ela — mesmo sem Claude Code, sem instalação nenhuma da parte dela.
4. No ciclo seguinte (até 10 minutos depois), o motor lê essa nota, registra a providência e já
   tenta produzir a minuta sozinho, headless.
5. Se conseguir, devolve o link da minuta como nota no mesmo card, pronta para revisão. Se não
   conseguir, devolve uma nota pedindo que você abra o Claude e continue.

Você só precisa abrir uma conversa no Claude quando: quer mexer manualmente numa tarefa, quer
revisar/aprovar (`revisar`), ou o motor avisou que não conseguiu concluir sozinho.

## Atualizações sem reinstalar

O mesmo prompt pode ser usado de novo quando houver versão nova. O Claude deve perceber que o
escritório já está configurado e executar `atualizar-kit`: compara `versao-kit.json` e
`manifesto-arquivos.json`, traz somente arquivos oficiais novos ou alterados e preserva dados do
escritório, fila, entregas, propostas, skills próprias, caminhos locais e credenciais. Havendo
personalização conflitante em arquivo oficial, mantém as duas versões para decisão sua.

## Checkpoints visuais

- `diagnosticar`: todos os itens críticos aparecem como `OK`.
- `contexto`: materializa uma pasta `entrada` privada com os autos obtidos do Sync.
- `status`: registra autor, horário, transição e hash da entrega.
- `promover-skill`: só aceita proposta de tarefa aprovada e nunca sobrescreve skill existente.

## Escritório real

O Kit inclui apenas contratos de conectores. A promoção para uso real exige edição consciente de
`escritorio.json`, revisão dos adaptadores e teste próprio. O Sync permanece somente leitura. Este
Kit não implementa protocolo automático. O adaptador Infinitum é uma interface opcional, não uma
integração ativa nem uma credencial embutida.

## Escolha do software jurídico

O assistente primeiro instala, diagnostica e comprova o núcleo Claude + GitHub. Somente depois
pergunta qual software você usa — Infinitum, Meu Estagiário, ADVBOX, Astrea, CPJ, ProJuris, outro ou
nenhum — e se você quer prosseguir agora com a instalação guiada. A integração opcional não interrompe
nem condiciona a instalação inicial. Nunca empurre um produto.

- Sem software: use a fila GitHub do núcleo.
- Infinitum: use o instalador portátil em `integracoes/infinitum/` e siga integralmente suas instruções.
- Meu Estagiário: use o instalador em `integracoes/meu-estagiario/`. Ele valida a API, registra a
  configuração apenas no computador, executa teste sintético e oferece espelhamento idempotente.
- ADVBOX: use o instalador em `integracoes/advbox/`. Você continua na ADVBOX; o Claude audita a API,
  completa pela interface os tipos de tarefa e os fluxos e configura a ponte que cria tarefas da
  Esteira dentro do próprio software.
- Outro software: localize a documentação oficial da API, guarde a chave localmente, compare as
  capacidades com o modelo ideal e não prometa o que a API não permite.

### Infinitum

O pacote integrado cria ou reutiliza o cadastro `Casos`, oito fases, quinze campos e duas automações.
É idempotente, não exclui estruturas e pode exigir que o agente configure `Casos` pela interface.
O token fica somente no computador. Instalar a estrutura não instala o worker que gera minutas;
revisão humana, aprovação jurídica e protocolo manual continuam separados.

### Meu Estagiário

O instalador valida identidade, escopos, membros, tipos de tarefa e etapas de caso contra a API ao
vivo. A configuração guarda apenas o nome da variável de credencial. O teste opcional cria uma tarefa
sintética, confirma por leitura de volta os estados `Em andamento` e `Em revisão`, escreve uma nota
técnica e arquiva o teste. `ponte.py` localiza o card pelo ID estável do Kit e cria ou atualiza sem
duplicar.

`ponte.py` sozinho é execução sob demanda, uma tarefa por chamada. Para o ciclo fechar sozinho, use
`motor.py` (`integracoes/meu-estagiario/pacote/motor.py`), instalado e agendado à parte, nunca junto
da instalação inicial. Uma vez agendado, o motor faz DUAS coisas a cada passada: (1) pega intimação
nova já em cache local (o auto-sync do núcleo consulta o Sync 1x/dia) e cria sozinho a tarefa + o
card correspondente no Meu Estagiário, sem esperar decisão nenhuma; (2) lê nota nova em qualquer card
já espelhado, registra como providência e já tenta produzir a minuta headless na mesma passada,
devolvendo o link como nota.

Quem opera o Kit (quem roda a esteira) é sempre você — isso não muda. Mas o card no Meu Estagiário
pode pertencer a QUALQUER pessoa real do seu time, mesmo sem Claude Code nenhum: a nota aceita uma
linha opcional `Responsável: <nome exato>`. Sem essa linha, o card continua no seu nome. Com ela, o
motor confere o nome contra o cadastro real do Meu Estagiário (só aceita correspondência exata — sem
isso, devolve uma nota pedindo o nome certo, nunca adivinha) e o card passa a aparecer para aquela
pessoa, mesmo a produção continuando a acontecer por baixo do mesmo jeito. É o trecho mais novo do
Kit; a primeira rodada deve ser acompanhada. Detalhe completo em
`integracoes/meu-estagiario/pacote/INSTRUCOES_AGENTE.md`.

### Advbox

O instalador é híbrido porque a API pública não cria tipos de tarefa nem toda a configuração do
Flowter. Ele lê `/settings`, identifica o que falta e conduz um usuário Gestor pela interface para
criar oito tarefas `[KIT3]` e três fluxos: produção/revisão, refação e protocolo manual. Uma captura
da configuração é registrada por hash antes da aprovação.

`ponte.py` cria na própria ADVBOX a próxima tarefa da Esteira, primeiro em simulação. A escrita é
limitada a `POST /posts`, usa marcador idempotente e exige leitura de volta por ID. O pacote não
altera cliente, processo, movimentação ou financeiro. O Sync continua sendo a fonte dos autos.

Esta versão é prévia: entrega estrutura e ponte sob demanda. Um worker contínuo ainda precisa ser
instalado posteriormente por polling da API ou webhook HTTP do Flowter e comprovado ponta a ponta
antes de ser anunciado como automático.

## Caixa de entrada de intimações

`checar-intimacoes` pagina as pendentes dos últimos 30 dias por operações GET e guarda somente os
dados necessários à triagem em `.intimacoes-inbox/`, fora do Git. O agendamento usa
`--somente-se-dia-novo`, portanto as demais sincronizações do mesmo dia não repetem a consulta. No
Windows, a tarefa também dispara no logon; no macOS, usa `RunAtLoad`.

O Kit nunca cria tarefas em lote sem decisão humana. Você escolhe uma intimação e informa a
providência; `importar-intimacao` cria uma única tarefa e deduplica pelo ID do Sync. A data sugerida
pelo Sync é armazenada como não confirmada, sem recálculo. O Kit não chama os endpoints de
tratar/reabrir, não altera monitoramento e não escreve no Sync.

## Segurança e contingência

- Nunca versione `.escritorio.local.json`, `.env`, autos, minutas reais ou certificados.
- Se o Git estiver indisponível, trabalhe no clone local e não simule que sincronizou.
- Se houver conflito (por exemplo, duas máquinas suas), não apague nenhum lado. O comando para e
  informa os arquivos.
- O auto-sync só atua com árvore limpa. Alterações ainda não commitadas ficam preservadas e a rodada
  é registrada como bloqueada; revise-as e crie o commit você mesmo.
- Se um documento estiver ausente, registre a lacuna na minuta e na revisão.
- Para desfazer uma instalação, remova apenas este clone; as configurações e credenciais externas não
  são alteradas pelo Kit.

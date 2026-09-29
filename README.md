# Kit 3 - Ligando o Motor da sua Esteira

Versão 3.0.0. Este Kit monta uma esteira de petições operada por **uma pessoa só** — você, o Dono,
num único Claude Code — com o **Meu Estagiário** como única interface para o resto da equipe. Não
existe convite, código de colaborador nem clone de segunda pessoa: sua equipe nunca abre GitHub nem
Claude Code, só o Meu Estagiário, como sempre usou.

📄 **[Veja o dia a dia explicado em linguagem simples, com analogias: `POP-DIA-A-DIA.md`](POP-DIA-A-DIA.md)**
— quem faz o quê, o que roda sozinho, o que ainda depende de você. Comece por ali se quiser entender
antes de instalar.

O repositório público deste Kit é apenas o molde, sem dados reais de nenhum caso. Durante a
instalação, o Claude cria um novo repositório **privado** para o seu escritório — a fonte canônica do
que você faz, sob sua própria conta do GitHub. O núcleo funciona mesmo sem nenhum software conectado:

`Sync (autos, leitura) → sua fila → você produz → você revisa → proposta → skill`

O Sync é obrigatório: é dele que vêm as intimações e os autos dos processos, sempre em modo leitura.
O Meu Estagiário é opcional e só entra depois de você comprovar que o núcleo já está funcionando. O
modo inicial é `mvp`: trabalha com tarefas reais e lê os autos no Sync, mas mantém bloqueada qualquer
escrita em sistema externo até você conectar algo de propósito.

Com o Meu Estagiário conectado, um **motor opcional** (instalado à parte, nunca junto do núcleo) fecha
o ciclo sozinho: intimação nova vira card sozinha, você escreve uma nota dizendo o que fazer, e o
motor produz a minuta headless e devolve o link como nota na mesma tarefa. Revisão humana e protocolo
manual continuam separados, sempre.

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
grave tokens na conversa ou no Git. Não conecte o Meu Estagiário nem habilite escrita em sistema
externo nesta etapa inicial. Ao final, rode o diagnóstico e mostre apenas o que está pronto e
qualquer ação pessoal inevitável.
```

## Como o trabalho acontece no dia a dia

O computador executa `iniciar-escritorio` uma única vez. Depois disso, o trabalho segue três
momentos — não são papéis diferentes, é você mesmo, em horas diferentes do dia:

1. **Triagem**: você olha as intimações novas (`checar-intimacoes`) e decide o que fazer com cada
   uma (`importar-intimacao`), ou cria uma tarefa direto (`criar-tarefa`).
2. **Execução**: você assume a tarefa (`assumir`), pega os autos (`contexto`), o Claude copia o
   modelo aprovado e produz a peça, e você registra a entrega (`entregar`).
3. **Revisão**: você aprova, pede ajuste ou reprova (`revisar`). Se aprender algo que vale a pena
   virar regra permanente, propõe (`propor-skill`) e depois promove (`promover-skill`).

A skill `executar-tarefa` cobre os três momentos. Toda mutação cria commit e sincroniza sozinha; se
houver conflito (por exemplo, você usando dois computadores), o Kit para e preserva os dois lados
para você decidir — nunca escolhe nem apaga nada sozinho.

## O que roda sozinho, e o que ainda depende de você abrir o Claude

Sem o Meu Estagiário conectado, o Kit é só o núcleo: nada cria tarefa sozinho, e você acompanha tudo
abrindo o Claude e mandando `/executar-tarefa Mostre minha fila e me ajude a executar a próxima
tarefa.`.

Com o Meu Estagiário conectado e o motor agendado, o ciclo diário roda sem você abrir o Claude:

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

## Conectar o Meu Estagiário (opcional, depois do núcleo)

O assistente primeiro instala, diagnostica e comprova o núcleo Claude + GitHub funcionando sozinho.
Só depois pergunta se você quer conectar o Meu Estagiário — o único software de gestão que este Kit
integra — e se quer fazer isso agora ou continuar só com o núcleo por enquanto. Essa etapa nunca
interrompe nem condiciona a instalação inicial.

Para conectar, use o instalador em `integracoes/meu-estagiario/` (skill `conectar-meu-estagiario`).
Ele confere sua conta de verdade contra a API do Meu Estagiário, guarda só o NOME da variável de
credencial (nunca a chave em si) e faz um teste sintético antes de declarar qualquer coisa pronta: cria
uma tarefa claramente marcada como teste, confirma por leitura de volta que ela mudou de status de
verdade, escreve uma nota avisando que é teste, e arquiva no final — nenhum caso real é tocado.
`ponte.py` liga cada card ao ID estável do Kit e nunca duplica.

`ponte.py` sozinho é sob demanda — espelha uma tarefa de cada vez, quando chamado. Para o ciclo
fechar sozinho, use `motor.py` (`integracoes/meu-estagiario/pacote/motor.py`), instalado e agendado à
parte, nunca junto da instalação inicial. Uma vez agendado, o motor faz DUAS coisas a cada passada:
(1) pega intimação nova já em cache local e cria sozinho a tarefa + o card correspondente, sem esperar
decisão nenhuma; (2) lê nota nova em qualquer card já espelhado, registra como providência e já tenta
produzir a minuta headless na mesma passada, devolvendo o link como nota.

Quem opera o Kit (quem roda a esteira) é sempre você — isso não muda. Mas o card pode pertencer a
QUALQUER pessoa real do seu time, mesmo sem Claude Code: a nota aceita uma linha opcional
`Responsável: <nome exato>`. Sem essa linha, o card continua no seu nome. Com ela, o motor confere o
nome contra o cadastro real do Meu Estagiário — só aceita correspondência exata, nunca adivinha — e o
card passa a aparecer para aquela pessoa, mesmo a produção continuando a acontecer por baixo do mesmo
jeito. É o trecho mais novo do Kit; a primeira rodada deve ser acompanhada. Detalhe completo em
`integracoes/meu-estagiario/pacote/INSTRUCOES_AGENTE.md`.

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

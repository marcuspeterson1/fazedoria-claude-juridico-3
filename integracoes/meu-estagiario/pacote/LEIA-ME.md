# Instalador da Esteira — Meu Estagiário

Este pacote conecta um clone privado já instalado do Kit 3 ao Meu Estagiário. Ele valida a conta e
os catálogos reais, registra a integração apenas na configuração local e inclui uma ponte
idempotente para espelhar tarefas do Kit no quadro do escritório.

O token nunca viaja no ZIP, no Git ou no resultado. Ele deve estar na variável
`MEU_ESTAGIARIO_API_KEY` ou ser informado no campo oculto aberto pelo instalador.

## Prompt para o aluno

> Descompacte este pacote, leia integralmente `INSTRUCOES_AGENTE.md` e assuma a instalação no meu
> clone privado do Kit 3. Não me mande usar terminal. Guarde a chave fora da conversa e do Git,
> valide a conta, configure a integração e faça o teste sintético. Não use casos reais, não mexa
> em financeiro ou skills e não protocole nada. Só conclua com `resultado_instalacao.json` aprovado.

## Auditoria

```bash
python3 -m unittest discover -s tests -v
python3 instalar.py --kit-root /caminho/do/clone --verify-only
```

O teste de escrita é opt-in: `--test-write`. Ele cria uma tarefa claramente sintética, confirma os
estados por leitura de volta, escreve uma nota técnica e arquiva o teste. Não apaga registros.

Para espelhar uma tarefa já existente do Kit:

```bash
python3 ponte.py /caminho/do/clone/fila/ID.json
```

A ponte usa um marcador estável para não duplicar cards. Se não localizar exatamente o caso ou a
pessoa responsável, preserva a tarefa sem esse vínculo e relata a lacuna.

## Motor — fecha o ciclo pelo próprio Meu Estagiário (opcional, avançado)

Sem o motor, o espelhamento é sempre manual (`ponte.py` chamado à mão). Com o motor instalado, DUAS
coisas passam a acontecer sozinhas, agendadas:

1. **Captação**: intimação nova que já chegou no cache local (o auto-sync do núcleo consulta o Sync
   1x/dia) vira tarefa e card no Meu Estagiário sem ninguém pedir — você só vai encontrar o card lá.
2. **Produção**: você responde ao card com uma **nota** dizendo o que fazer; o motor lê essa nota,
   registra a providência na fila do Kit e, na mesma passada, dispara headless a mesma skill que
   você rodaria (`/resumo-do-processo` + `/gerar-peticao-por-modelo`), devolvendo o link da minuta
   como nota na mesma tarefa.

Quem opera o Kit é sempre você — isso não muda. Mas o card pode pertencer a outra pessoa real do
seu time, mesmo sem Claude Code: inclua na nota uma linha `Responsável: <nome exato>` e o motor
confere contra o cadastro do Meu Estagiário (só aceita nome que bate exatamente; sem isso, pede
correção em vez de adivinhar) e reatribui o card. Sem essa linha, o card fica com você. Nada disso
protocola nem pula a revisão humana.

```bash
python3 motor.py ciclo --kit-root /caminho/do/clone           # uma passada manual, pra testar
python3 motor.py instalar-agendamento --kit-root /caminho/do/clone   # agenda a cada 10 minutos
```

Isso é o pedaço mais novo e menos comprovado em campo do Kit — a primeira rodada real de cada
escritório deveria ser acompanhada, não deixada 100% sozinha. Detalhes e limites em
`INSTRUCOES_AGENTE.md`.

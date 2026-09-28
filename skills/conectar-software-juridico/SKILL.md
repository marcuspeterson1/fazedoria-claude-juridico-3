---
name: conectar-software-juridico
description: Instala de forma guiada a integração opcional do Kit 3 com Meu Estagiário, Advbox legada ou Infinitum.
---

# Conectar software jurídico

Pergunte uma coisa por vez. Primeiro identifique o sistema: Meu Estagiário, Advbox ou Infinitum.
Explique que o Sync continua sendo a fonte obrigatória e somente leitura dos autos; o software de
gestão organiza tarefas, responsáveis, revisão e entrega.

Antes de agir, confira se o Kit está num clone privado e já configurado. Leia integralmente o
`README.md` e o `INSTRUCOES_AGENTE.md` do pacote escolhido em `integracoes/`.

- Meu Estagiário: use o pacote público correspondente, valide os escopos e execute o teste sintético.
  A ponte é idempotente, mas não equivale a um worker contínuo.
- ADVBOX: assuma que o aluno continuará no sistema. Use o instalador híbrido para auditar a API,
  criar pela interface os tipos `[KIT3]` e os fluxos ausentes e validar com evidência. A ponte pode
  criar tarefas em `/posts`, sempre após simulação, com marcador idempotente e leitura de volta.
  Não altere processos, clientes, movimentações ou financeiro.
- Infinitum: siga o instalador portátil existente e seus gates.

Nunca peça token na conversa ou o grave no Git. Use caixa segura ou secret store local. Só declare
conclusão após teste, leitura de volta e `resultado_instalacao.json` aprovado. Diferencie configuração
local, commit/sincronização, worker implantado e execução comprovada. Protocolo permanece manual.

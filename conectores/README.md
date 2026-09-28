# Contratos de conectores

O Sync é a fonte obrigatória dos autos e opera somente em leitura. Os conectores de gestão são
opcionais e só podem espelhar tarefas ou entregas depois de configuração consciente, com
idempotência, revisão humana e confirmação do resultado.

- Meu Estagiário: espelho operacional de tarefas, com leitura de volta obrigatória.
- ADVBOX: para o aluno que permanece no sistema, pode ser a fila operacional após instalação
  consciente; a escrita fica limitada à criação idempotente de tarefas `[EURO]`.
- Infinitum: estrutura opcional instalada pelo pacote portátil próprio.

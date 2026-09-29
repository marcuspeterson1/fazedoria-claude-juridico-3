# Contratos de conectores

O Sync é a fonte obrigatória dos autos e opera somente em leitura — é de lá que vêm as intimações e
os documentos do processo, e o Kit nunca escreve nada de volta nele.

O Meu Estagiário é o único conector de gestão deste Kit: um espelho operacional das tarefas, com
leitura de volta obrigatória depois de qualquer escrita (nunca confia em "deu 200", sempre confere
se realmente gravou). Configuração consciente, idempotência e revisão humana sempre.

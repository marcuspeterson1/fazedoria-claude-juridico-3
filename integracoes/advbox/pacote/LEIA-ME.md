# Instalador prévio da Esteira — ADVBOX

Este pacote é para o escritório que usa ADVBOX e continuará usando ADVBOX. A fila operacional, as
tarefas, os responsáveis, o histórico e a revisão permanecem dentro do software. O Sync fornece os
autos em somente leitura e o Claude produz a minuta a partir de modelo aprovado.

O instalador é híbrido: audita a conta pela API, identifica os tipos de tarefa ausentes e ensina o
Claude a completar pela interface as partes que a API pública não cria. Depois oferece `ponte.py`
para criar as tarefas da Esteira na própria ADVBOX sem duplicação.

## Prompt para o aluno

Use `PROMPT_PARA_O_ALUNO.txt`. O aluno não precisa abrir terminal. Um Gestor da conta precisa estar
presente para criar tipos de tarefa e Flowter/Workflow e para escolher responsáveis e prazos.

## Limite atual

Esta é uma versão prévia: instala a linguagem operacional e a ponte da Esteira, mas ainda não instala
um worker contínuo. O worker poderá usar polling da API ou HTTP Request do Flowter para n8n/VPS.
Protocolo continua manual.

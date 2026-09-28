# ADVBOX — Esteira dentro do software do aluno

Este pacote é destinado ao aluno que continuará operando na ADVBOX. Ele audita os catálogos pela
API, gera o plano de configuração, orienta o Claude na criação dos tipos de tarefa e Flowter pela
interface e inclui uma ponte idempotente para criar as próximas tarefas da Esteira na própria
ADVBOX.

É uma versão prévia porque a API documentada não cria tipos de tarefa/Flowter e não expõe conclusão
de tarefas. Esses pontos permanecem guiados/humanos. Um worker contínuo é camada posterior.

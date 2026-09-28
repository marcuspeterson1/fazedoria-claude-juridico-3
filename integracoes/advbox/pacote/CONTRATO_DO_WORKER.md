# Contrato prévio do worker ADVBOX

```text
ADVBOX: [EURO] PRODUZIR MINUTA COM CLAUDE
  → identificar processo e CNJ
  → Sync: ler autos completos, somente leitura
  → copiar modelo aprovado
  → gerar minuta e conferir arquivo
  → ADVBOX: criar [EURO] REVISAR MINUTA com link e marcador
       ├─ corrigir → [EURO] REFAZER MINUTA COM CLAUDE
       └─ aprovar → [EURO] APROVADA PARA PROTOCOLO
                    → [EURO] PROTOCOLAR MANUALMENTE
                    → [EURO] CONFIRMAR PROTOCOLO
```

Cada transição é uma nova tarefa rastreável na ADVBOX. Use `ponte.py`, ID externo idempotente e
leitura de volta. O worker nunca calcula prazo fatal sem fonte, nunca altera autos, nunca redige sem
modelo aprovado e nunca conclui a tarefa de protocolo. Como a API pública não documenta conclusão
ou edição de tarefa, esses atos continuam humanos até existir contrato oficial comprovado.

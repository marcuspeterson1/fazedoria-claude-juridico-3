# Contrato prévio do worker ADVBOX

```text
ADVBOX: [KIT3] PRODUZIR MINUTA COM CLAUDE
  → identificar processo e CNJ
  → Sync: ler autos completos, somente leitura
  → copiar modelo aprovado
  → gerar minuta e conferir arquivo
  → ADVBOX: criar [KIT3] REVISAR MINUTA com link e marcador
       ├─ corrigir → [KIT3] REFAZER MINUTA COM CLAUDE
       └─ aprovar → [KIT3] APROVADA PARA PROTOCOLO
                    → [KIT3] PROTOCOLAR MANUALMENTE
                    → [KIT3] CONFIRMAR PROTOCOLO
```

Cada transição é uma nova tarefa rastreável na ADVBOX. Use `ponte.py`, ID externo idempotente e
leitura de volta. O worker nunca calcula prazo fatal sem fonte, nunca altera autos, nunca redige sem
modelo aprovado e nunca conclui a tarefa de protocolo. Como a API pública não documenta conclusão
ou edição de tarefa, esses atos continuam humanos até existir contrato oficial comprovado.

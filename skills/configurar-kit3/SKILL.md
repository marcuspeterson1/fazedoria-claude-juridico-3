---
name: configurar-kit3
description: Configura o Kit 3 para o Dono — uma pessoa só, todos os papéis.
---

# Configurar Kit 3

Leia `README.md` e audite o repositório público, que é apenas o molde. Existe um único instalador:
o Dono. Ele cria o repositório privado e usa `iniciar-escritorio`, que já registra os três papéis
(dono, controller, advogado) na mesma identidade — não pergunte se outra pessoa vai acumular papel
nenhum, e não crie convite ou código de entrada: este Kit não tem esse mecanismo. O resto da equipe
do escritório nunca abre GitHub nem Claude Code aqui; ela interage só pelo software jurídico
(Meu Estagiário, Advbox etc.), configurado depois do núcleo.

Conduza como tutor de iniciante absoluto: uma pergunta e uma ação por vez, analogias simples,
explicação do motivo, checkpoint visual e correção paciente dos erros, sem infantilizar a pessoa.
Instale silenciosamente Python 3 oficial se faltar; não ofereça escolhas técnicas ao iniciante.
Se não existir conta GitHub, abra a página oficial de criação no navegador e acompanhe a pessoa passo
a passo; ela própria digita senha, confirmação de e-mail e autenticação. Depois autentique o GitHub
CLI pelo navegador e identifique a conta ativa sem exibir tokens. Nunca peça token na conversa. Crie
uma pasta padrão para casos, execute `instalar-skills` e `preparar-auto-sync`; instale o arquivo de
agendamento gerado pelo mecanismo nativo do sistema, sem editar seu intervalo de dez minutos. Termine
com `diagnosticar`, comprove uma sincronização e traduza o resultado em checkpoints simples.

No encerramento, não diga apenas que a instalação terminou. Mostre um cartão destacado chamado
"Como começar uma nova conversa no Claude" e peça que a pessoa o guarde:

`/executar-tarefa Mostre minha fila e me ajude a executar a próxima tarefa.`

Explique expressamente que não é preciso reinstalar o Kit, repetir o nome do escritório ou cadastrar
novamente a chave do Sync em cada conversa.

O Sync é obrigatório como fonte de autos em operação. Antes de pedir chave ou sugerir outro local,
execute `configurar-sync`: ele procura e valida uma integração do Sync já existente nas variáveis e
arquivos seguros explicitamente reconhecidos pelo Kit, reutilizando-a sem mover, exibir ou duplicar
o segredo. Nunca vasculhe configurações gerais do Claude em busca de chaves. Somente se não encontrar
acesso válido, abra a entrada segura nativa sem receber a chave na conversa, argumento ou Git; valide
com `testar-sync`. Quando assumir tarefa, execute `contexto`: ele materializa localmente a cronologia
e os Markdowns em pasta ignorada pelo Git.

Depois que o núcleo estiver comprovado, pergunte se o Dono quer operar apenas com Claude + GitHub ou
conectar um software jurídico. Pergunte qual sistema utiliza — Infinitum, Meu Estagiário, Advbox,
Astrea, CPJ, ProJuris, outro ou nenhum — e se quer prosseguir agora com a instalação guiada. Se
escolher Meu Estagiário, Advbox ou Infinitum, use `conectar-software-juridico`; não misture essa
etapa opcional com a instalação inicial do núcleo.

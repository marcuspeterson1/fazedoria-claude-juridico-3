#!/usr/bin/env python3
"""Ensaio determinístico do escritório operado por uma única pessoa (Kit 3)."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SOURCE = Path(__file__).parents[1]
os.environ["KIT3_NO_AUTO_GIT"] = "1"
CASES = [
    ("01-caso-nascimento", "0000001-00.2099.0.00.0001", "criar primeira minuta e skill candidata"),
    ("02-caso-validacao", "0000002-00.2099.0.00.0002", "validar invariantes e variáveis"),
    ("03-caso-fronteira", "0000003-00.2099.0.00.0003", "testar fronteira sem reabrir mérito"),
]

def run(cwd, *args, capture=False):
    result = subprocess.run(args, cwd=cwd, text=True, capture_output=capture)
    if result.returncode:
        print(result.stdout, result.stderr, file=sys.stderr)
        raise SystemExit(f"Falhou em {cwd}: {' '.join(args)}")
    return result.stdout.strip() if capture else ""

def git(cwd, *args):
    return run(cwd, "git", *args, capture=True)

with tempfile.TemporaryDirectory(prefix="kit3-ensaio-") as tmp:
    base = Path(tmp)
    seed = base / "seed"
    shutil.copytree(SOURCE, seed, ignore=shutil.ignore_patterns(".git", "__pycache__", ".escritorio.local.json"))
    git(seed, "init", "-b", "main")
    git(seed, "config", "user.name", "Origem do Kit")
    git(seed, "config", "user.email", "seed@example.invalid")
    git(seed, "add", ".")
    git(seed, "commit", "-m", "kit 3 base")
    bare = base / "privado.git"
    git(base, "clone", "--bare", str(seed), str(bare))
    escritorio = base / "escritorio"
    git(base, "clone", str(bare), str(escritorio))
    git(escritorio, "config", "user.name", "Marcus Peterson"); git(escritorio, "config", "user.email", "marcus@example.invalid")

    run(escritorio, sys.executable, "esteira.py", "iniciar-escritorio", "--nome", "Marcus Peterson",
        "--escritorio", "Escritório Exemplo", "--agente", "claude", "--repositorio", str(bare))
    run(escritorio, sys.executable, "esteira.py", "configurar-documentos", "--onde-modelos", "Pasta de modelos aprovados",
        "--pastas-clientes", "sim", "--destino-copia", "Pasta do cliente", "--padrao-nomes", "TIPO - CLIENTE - DATA")
    git(escritorio, "add", "escritorio.json"); git(escritorio, "commit", "-m", "configura escritório"); git(escritorio, "push")
    links = base / "perfis"
    run(escritorio, sys.executable, "esteira.py", "instalar-skills", "--destino-base", str(links))
    if not (links / ".claude/skills/executar-tarefa/SKILL.md").is_file() or not (links / ".agents/skills/executar-tarefa/SKILL.md").is_file():
        raise SystemExit("Skills não ficaram disponíveis.")
    run(escritorio, sys.executable, "esteira.py", "preparar-auto-sync")
    if not (escritorio / ".esteira-runtime/auto-sync.py").is_file():
        raise SystemExit("Runner de auto-sync não foi preparado.")
    run(escritorio, sys.executable, "esteira.py", "diagnosticar")

    task_ids = []
    for index, (ref, cnj, providencia) in enumerate(CASES, 1):
        task_id = run(escritorio, sys.executable, "esteira.py", "criar-tarefa", "--cnj", cnj,
                       "--referencia", ref, "--providencia", providencia, capture=True)
        task_ids.append(task_id)
        git(escritorio, "add", "fila"); git(escritorio, "commit", "-m", f"fila: caso {index}"); git(escritorio, "push")
        run(escritorio, sys.executable, "esteira.py", "assumir", task_id)
        draft = base / f"minuta-{index}.md"
        draft.write_text(f"<!-- RASCUNHO: NÃO PROTOCOLAR -->\n# Rodada {index}\n\nProvidência sugerida sujeita a revisão: {providencia}.\n", encoding="utf-8")
        run(escritorio, sys.executable, "esteira.py", "entregar", task_id, str(draft), "--modelo", "modelo-aprovado.docx", "--copia-destino", draft.name)
        git(escritorio, "add", "fila", "entregas"); git(escritorio, "commit", "-m", f"entrega caso {index}"); git(escritorio, "push")
        run(escritorio, sys.executable, "esteira.py", "revisar", task_id, "aprovada", "--feedback", f"Rodada técnica {index} aprovada.")
        git(escritorio, "add", "fila"); git(escritorio, "commit", "-m", f"revisa caso {index}"); git(escritorio, "push")
        if index == 1:
            proposal = base / "skill-candidata.md"
            proposal.write_text("# Método\n\nIdentificar o ato, conferir se já houve réplica e escolher entre impugnação completa ou manifestação curta. Manter revisão humana.\n", encoding="utf-8")
            run(escritorio, sys.executable, "esteira.py", "propor-skill", task_id, "--nome", "manifestacao-pos-contestacao", "--arquivo", str(proposal))
            git(escritorio, "add", "propostas"); git(escritorio, "commit", "-m", "skill: propõe candidata após caso 1"); git(escritorio, "push")
            proposal_name = next((escritorio / "propostas").glob("manifestacao-pos-contestacao--*.md")).name
            run(escritorio, sys.executable, "esteira.py", "promover-skill", proposal_name)
            git(escritorio, "add", "skills"); git(escritorio, "commit", "-m", "skill: promove candidata revisada"); git(escritorio, "push")

    if git(escritorio, "status", "--porcelain"):
        raise SystemExit(f"Clone terminou sujo: {escritorio}")

    print("ENSAIO OK — 1 identidade, 3 tarefas aprovadas e 1 skill candidata promovida.")

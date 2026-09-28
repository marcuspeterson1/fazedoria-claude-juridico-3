#!/usr/bin/env python3
"""CLI sem dependências do Kit 3 — Esteira de Petições operada por uma única pessoa."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import platform
import getpass
from datetime import datetime, timezone
from pathlib import Path

from conectores import sync as sync_connector

ROOT = Path(__file__).resolve().parent
LOCAL = ROOT / ".escritorio.local.json"
SHARED = ROOT / "escritorio.json"
INBOX_DIR = ROOT / ".intimacoes-inbox"
INBOX_STATE = INBOX_DIR / "intimacoes.json"
VALID_AGENTS = {"claude", "codex"}
TRANSITIONS = {
    "aberta": {"em_execucao"},
    "em_execucao": {"entregue"},
    "entregue": {"aprovada", "ajustes", "reprovada"},
    "ajustes": {"em_execucao"},
}

def hidden_subprocess_kwargs():
    """Evita janelas de console dos subprocessos no Windows."""
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if platform.system() == "Windows" else {}

def configure_git_credentials():
    """Liga o Git à autenticação já aprovada no GitHub CLI, quando disponível."""
    gh = shutil.which("gh")
    if not gh:
        return
    subprocess.run([gh, "auth", "setup-git"], capture_output=True, **hidden_subprocess_kwargs())

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def load(path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)

def repo_url():
    result = subprocess.run(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True, capture_output=True)
    return result.stdout.strip() if result.returncode == 0 else ""

def auto_git(paths, message):
    if os.getenv("KIT3_NO_AUTO_GIT") == "1" or not (ROOT / ".git").exists(): return
    local = load(LOCAL) if LOCAL.exists() else {}
    if not local.get("sincronizacao_automatica", True): return
    configure_git_credentials()
    quiet = hidden_subprocess_kwargs()
    subprocess.run(["git", "add", "--", *paths], cwd=ROOT, check=True, capture_output=True, **quiet)
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT, **quiet).returncode:
        subprocess.run(["git", "commit", "-m", message], cwd=ROOT, check=True, capture_output=True, **quiet)
    pull = subprocess.run(["git", "pull", "--rebase"], cwd=ROOT, capture_output=True, text=True, **quiet)
    if pull.returncode:
        subprocess.run(["git", "rebase", "--abort"], cwd=ROOT, capture_output=True, **quiet)
        raise SystemExit("Sincronização encontrou conflito. As duas versões foram preservadas para conciliação.")
    if subprocess.run(["git", "push"], cwd=ROOT, capture_output=True, **quiet).returncode:
        raise SystemExit("A alteração ficou salva neste computador, mas o envio automático ao histórico falhou.")

def pull_before_read():
    if os.getenv("KIT3_NO_AUTO_GIT") == "1" or not (ROOT / ".git").exists(): return
    configure_git_credentials()
    quiet = hidden_subprocess_kwargs()
    if subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, **quiet).stdout: return
    pull = subprocess.run(["git", "pull", "--rebase"], cwd=ROOT, capture_output=True, text=True, **quiet)
    if pull.returncode:
        raise SystemExit("Não foi possível confirmar a fila remota. A fila local pode estar desatualizada; corrija a autenticação/sincronização antes de listar.")

def config():
    if not LOCAL.exists():
        raise SystemExit("Configuração local ausente. Execute: python3 esteira.py iniciar-escritorio")
    return load(LOCAL), load(SHARED)

def print_daily_card(local):
    print("\nCOMO COMEÇAR UMA NOVA CONVERSA NO CLAUDE:")
    print('/executar-tarefa Mostre minha fila e me ajude a executar a próxima tarefa.')
    if INBOX_STATE.exists():
        inbox = load(INBOX_STATE)
        novas = sum(1 for item in inbox.get("intimacoes", {}).values()
                    if not item.get("importada_em") and item.get("nova", False))
        if novas:
            print(f"CAIXA DE ENTRADA: {novas} intimação(ões) nova(s) aguardando triagem.")
    print("Não reinstale o Kit e não informe novamente o nome do escritório ou a chave do Sync.")

def task_path(task_id):
    path = ROOT / "fila" / f"{task_id}.json"
    if not path.exists():
        raise SystemExit(f"Tarefa não encontrada: {task_id}")
    return path

def task(task_id):
    return load(task_path(task_id))

def event(data, action, actor, detail=""):
    data.setdefault("historico", []).append({"em": now(), "acao": action, "por": actor, "detalhe": detail})

def transition(data, target):
    current = data["status"]
    if target not in TRANSITIONS.get(current, set()):
        raise SystemExit(f"Transição inválida: {current} → {target}")
    data["status"] = target

def cmd_start_office(a):
    shared = load(SHARED)
    org = shared.get("organizacao") or {}
    if org.get("id") and org.get("dono") != a.nome:
        raise SystemExit("Este escritório já tem um Dono/Administrador registrado.")
    if not org.get("id"):
        import uuid
        shared["nome_escritorio"] = a.escritorio
        shared["organizacao"] = {"id": str(uuid.uuid4()), "dono": a.nome,
                                 "repositorio": a.repositorio or repo_url(), "criada_em": now()}
        if not shared["organizacao"]["repositorio"]: raise SystemExit("Repositório privado não identificado.")
        save(SHARED, shared)
    previous = load(LOCAL) if LOCAL.exists() else {}
    local = {"schema_version": 1, "colaborador": a.nome, "papeis": ["dono", "controller", "advogado"],
             "agente": a.agente, "repositorio_privado_confirmado": True, "sincronizacao_automatica": True,
             "organizacao_id": shared["organizacao"]["id"],
             "raizes_entrada": previous.get("raizes_entrada", {}), "configurado_em": now()}
    save(LOCAL, local)
    auto_git([str(SHARED.relative_to(ROOT))], "config: iniciar escritório")
    print("OK — escritório criado. Você:", a.nome, "— acumula todos os papéis (sozinho, sem colaborador no Kit).")
    print_daily_card(local)

def cmd_configure_documents(a):
    local, shared = config()
    shared["producao_documental"] = {
        "modelo_obrigatorio": True,
        "onde_ficam_modelos": a.onde_modelos,
        "pastas_clientes_existem": a.pastas_clientes == "sim",
        "destino_da_copia": a.destino_copia,
        "padrao_nomes": a.padrao_nomes,
        "preservar_identidade_visual": True,
        "preservar_topicos_aplicaveis": True,
        "configurado_por": local["colaborador"],
        "configurado_em": now(),
    }
    save(SHARED, shared)
    if a.caminho_local_modelos:
        local.setdefault("producao_documental_local", {})["caminho_modelos"] = a.caminho_local_modelos
    if a.caminho_local_clientes:
        local.setdefault("producao_documental_local", {})["caminho_clientes"] = a.caminho_local_clientes
    save(LOCAL, local)
    auto_git([str(SHARED.relative_to(ROOT))], "config: registrar padrão documental do escritório")
    print("OK — padrão documental registrado.")
    print("OK — caminhos desta máquina ficaram somente na configuração local, fora do Git.")

def cmd_diagnose(_a):
    checks = []
    checks.append((SHARED.exists(), "configuração compartilhada existe"))
    checks.append((LOCAL.exists(), "configuração local existe e está ignorada"))
    try:
        local, shared = config()
        checks += [
            (shared.get("modo") == "mvp", "modo MVP ativo"),
            (shared.get("gates", {}).get("protocolo_manual") is True, "protocolo continua manual"),
            (set(local.get("papeis") or []) == {"dono", "controller", "advogado"}, "papéis completos, uma pessoa só"),
            (local.get("agente") in VALID_AGENTS, "agente local válido"),
            (local.get("repositorio_privado_confirmado") is True, "repositório privado confirmado"),
            (shared.get("conectores", {}).get("sync", {}).get("somente_leitura") is True, "Sync limitado a somente leitura"),
            (shared.get("producao_documental", {}).get("modelo_obrigatorio") is True, "petição exige modelo aprovado"),
            (shared.get("producao_documental", {}).get("onde_ficam_modelos") not in (None, "", "CONFIGURE-ME"), "localização dos modelos definida"),
            (shared.get("producao_documental", {}).get("destino_da_copia") not in (None, "", "CONFIGURE-ME"), "destino da cópia definido"),
            (shared.get("producao_documental", {}).get("padrao_nomes") not in (None, "", "CONFIGURE-ME"), "padrão de nomes definido"),
        ]
    except (SystemExit, KeyError, json.JSONDecodeError):
        pass
    ignored = subprocess.run(["git", "check-ignore", "-q", str(LOCAL)], cwd=ROOT).returncode == 0 if (ROOT / ".git").exists() else True
    checks.append((ignored, "segredos/configuração local fora do Git"))
    for ok, label in checks:
        print(("OK" if ok else "FALHA"), "—", label)
    if not all(ok for ok, _ in checks):
        raise SystemExit(1)
    print_daily_card(local)

def slug(value):
    value = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip()).strip("-").lower()
    return value or "tarefa"

def cmd_create(a):
    local, shared = config()
    if local.get("repositorio_privado_confirmado") is not True:
        raise SystemExit("BLOQUEADO: crie/conecte e confirme o repositório privado antes de registrar tarefas.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"{stamp}-{slug(a.referencia)}"
    data = {"schema_version": 1, "id": task_id, "status": "aberta", "modo": shared["modo"],
            "cnj": a.cnj, "referencia_entrada": a.referencia, "fonte": "sync",
            "providencia_sugerida": a.providencia, "responsavel": local["colaborador"],
            "criada_por": local["colaborador"], "criada_em": now(), "entrega": None,
            "revisao": None, "historico": []}
    event(data, "criada", local["colaborador"], "Providência é sugestão sujeita à revisão humana.")
    save(ROOT / "fila" / f"{task_id}.json", data)
    auto_git([f"fila/{task_id}.json"], f"fila: criar {task_id}")
    print(task_id)

def _inbox_vazio(organizacao_id):
    return {"schema_version": 1, "organizacao_id": organizacao_id,
            "ultima_consulta_dia": None, "ultima_consulta_em": None, "intimacoes": {}}

def atualizar_inbox_intimacoes(local, cliente=None, somente_se_dia_novo=False, hoje=None):
    """Atualiza cache local por GET; não cria tarefas nem escreve no Sync."""
    hoje = hoje or datetime.now().astimezone().date().isoformat()
    if INBOX_STATE.exists():
        inbox = load(INBOX_STATE)
        if inbox.get("organizacao_id") != local["organizacao_id"]:
            inbox = _inbox_vazio(local["organizacao_id"])
    else:
        inbox = _inbox_vazio(local["organizacao_id"])
    if somente_se_dia_novo and inbox.get("ultima_consulta_dia") == hoje:
        return inbox, 0, False
    cliente = cliente or sync_connector.ClienteSync(
        sync_connector.carregar_chave(local["organizacao_id"]))
    recebidas = cliente.intimacoes(status="pendentes", dias=30)
    registros = inbox.setdefault("intimacoes", {})
    novas = 0
    for item in recebidas:
        if item.get("id") is None:
            continue
        chave = str(item["id"])
        anterior = registros.get(chave) or {}
        if not anterior:
            novas += 1
        registros[chave] = {
            "id": item["id"], "processo": item.get("processo"),
            "tribunal": item.get("tribunal"), "data": item.get("data"),
            "tipo_ato": item.get("tipo_ato"), "resumo": item.get("resumo"),
            "requer_manifestacao": item.get("requer_manifestacao"),
            "data_fatal_sync": item.get("data_fatal"), "prazo_ato_sync": item.get("prazo_ato"),
            "vista_primeiro_em": anterior.get("vista_primeiro_em") or now(),
            "importada_em": anterior.get("importada_em"),
            "tarefa_id": anterior.get("tarefa_id"),
            "nova": anterior.get("nova", True),
        }
    inbox["ultima_consulta_dia"] = hoje
    inbox["ultima_consulta_em"] = now()
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    save(INBOX_STATE, inbox)
    return inbox, novas, True

def cmd_check_intimations(a):
    local, _shared = config()
    try:
        inbox, novas, consultou = atualizar_inbox_intimacoes(
            local, somente_se_dia_novo=a.somente_se_dia_novo)
    except RuntimeError as exc:
        raise SystemExit(f"Não foi possível consultar as intimações no Sync: {exc}")
    pendentes = [item for item in inbox.get("intimacoes", {}).values()
                 if not item.get("importada_em")]
    pendentes.sort(key=lambda item: (item.get("data_fatal_sync") or "9999", item.get("data") or ""))
    if a.silencioso:
        print(f"INBOX_SYNC consultou={'sim' if consultou else 'nao'} novas={novas} pendentes={len(pendentes)}")
        return
    print("ID SYNC | DATA | PROCESSO | ATO | DATA SUGERIDA PELO SYNC")
    for item in pendentes:
        print(" | ".join(str(value or "—") for value in (
            item["id"], item.get("data"), item.get("processo"),
            item.get("tipo_ato"), item.get("data_fatal_sync"))))
    print(f"CHECKPOINT — {novas} nova(s); {len(pendentes)} aguardando triagem.")
    print("A data do Sync é referência sujeita à conferência humana; nenhum prazo foi recalculado.")
    print("Nenhuma intimação foi marcada como tratada e nenhuma tarefa foi criada automaticamente.")

def cmd_import_intimation(a):
    local, shared = config()
    if not INBOX_STATE.exists():
        raise SystemExit("Caixa de entrada ausente. Consulte as intimações antes de importar.")
    inbox = load(INBOX_STATE)
    chave = str(a.id_sync)
    item = inbox.get("intimacoes", {}).get(chave)
    if not item:
        raise SystemExit("Intimação não encontrada na caixa local; atualize a consulta.")
    if item.get("tarefa_id") and (ROOT / "fila" / f"{item['tarefa_id']}.json").exists():
        print("OK — intimação já vinculada à tarefa:", item["tarefa_id"])
        return
    for path in (ROOT / "fila").glob("*.json"):
        existente = load(path)
        if str(existente.get("intimacao_sync_id") or "") == chave:
            item.update({"tarefa_id": existente["id"], "importada_em": item.get("importada_em") or now(), "nova": False})
            save(INBOX_STATE, inbox)
            print("OK — intimação já vinculada à tarefa:", existente["id"])
            return
    cnj = item.get("processo")
    if not cnj:
        raise SystemExit("A intimação não trouxe número de processo; não foi criada tarefa.")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    task_id = f"{stamp}-intimacao-sync-{chave}"
    data = {"schema_version": 1, "id": task_id, "status": "aberta", "modo": shared["modo"],
            "cnj": cnj, "referencia_entrada": f"Intimação Sync {chave}", "fonte": "sync",
            "intimacao_sync_id": item["id"], "data_fatal_sync_nao_confirmada": item.get("data_fatal_sync"),
            "providencia_sugerida": a.providencia, "responsavel": local["colaborador"],
            "criada_por": local["colaborador"], "criada_em": now(), "entrega": None,
            "revisao": None, "historico": []}
    event(data, "criada_de_intimacao", local["colaborador"],
          "Sync somente leitura; prazo e providência sujeitos à conferência humana.")
    save(ROOT / "fila" / f"{task_id}.json", data)
    item.update({"tarefa_id": task_id, "importada_em": now(), "nova": False})
    save(INBOX_STATE, inbox)
    auto_git([f"fila/{task_id}.json"], f"fila: importar intimação Sync {chave}")
    print("OK — tarefa criada após confirmação:", task_id)
    print("OK — nenhuma alteração foi feita no Sync; protocolo continua manual.")

def cmd_assign(a):
    local, _ = config()
    data = task(a.id)
    if data["status"] != "aberta":
        raise SystemExit("Só é possível preparar automação em tarefas ainda abertas.")
    if a.providencia:
        data["providencia_sugerida"] = a.providencia
    if a.responsavel:
        # Quem opera o Kit continua sendo sempre o Dono (campo "advogado", fixado em cmd_claim).
        # "responsavel" aqui é só quem deve RECEBER o card no software jurídico conectado — pode
        # ser qualquer pessoa do time real, mesmo sem Claude Code.
        data["responsavel"] = a.responsavel
    if a.automatizar:
        data["automatizar"] = True
    event(data, "providencia_atualizada", local["colaborador"], a.providencia or "")
    save(task_path(a.id), data)
    auto_git([f"fila/{a.id}.json"], f"fila: providência {a.id}")
    print("OK — providência registrada.")

def cmd_list(a):
    pull_before_read()
    rows = []
    for p in sorted((ROOT / "fila").glob("*.json")):
        data = load(p)
        if not a.status or data["status"] == a.status:
            rows.append((data["id"], data["status"], data.get("responsavel") or "—", data["cnj"]))
    print("ID | STATUS | RESPONSÁVEL | CNJ")
    for row in rows:
        print(" | ".join(row))

def cmd_claim(a):
    local, _ = config()
    data = task(a.id)
    transition(data, "em_execucao")
    data["advogado"] = local["colaborador"]
    event(data, "assumida", local["colaborador"])
    save(task_path(a.id), data)
    auto_git([f"fila/{a.id}.json"], f"fila: assumir {a.id}")
    print("OK — tarefa assumida:", a.id)

def resolve_context(data, local):
    destino = ROOT / ".contextos-autos" / data["id"] / "entrada"
    try:
        return sync_connector.materializar_entrada(data["cnj"], destino, local["organizacao_id"])
    except RuntimeError as exc:
        raise SystemExit(f"Não foi possível preparar os autos pelo Sync: {exc}")

def cmd_context(a):
    local, _ = config()
    data = task(a.id)
    if data.get("advogado") != local["colaborador"]:
        raise SystemExit("Assuma a tarefa antes de abrir o contexto.")
    path = resolve_context(data, local)
    print("ENTRADA AUTORIZADA:", path)

def cmd_submit(a):
    local, _ = config()
    data = task(a.id)
    if data.get("advogado") != local["colaborador"]:
        raise SystemExit("Assuma a tarefa antes de entregar.")
    source = Path(a.arquivo).expanduser().resolve()
    if not source.is_file():
        raise SystemExit("Arquivo de entrega não encontrado.")
    _local_cfg, shared = config()
    policy = shared.get("producao_documental") or {}
    if policy.get("modelo_obrigatorio", True) and (not a.modelo or not a.copia_destino):
        raise SystemExit("BLOQUEADO: informe o modelo aprovado copiado e o destino da cópia. A peça não pode nascer em branco.")
    target_dir = ROOT / "entregas" / a.id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / source.name
    target.write_bytes(source.read_bytes())
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    transition(data, "entregue")
    data["entrega"] = {"arquivo": str(target.relative_to(ROOT)), "sha256": digest, "em": now(), "por": local["colaborador"],
                       "modelo_utilizado": a.modelo, "copia_destino": a.copia_destino}
    event(data, "entregue", local["colaborador"], f"sha256:{digest}")
    save(task_path(a.id), data)
    auto_git([f"fila/{a.id}.json", f"entregas/{a.id}"], f"fila: entregar {a.id}")
    print("OK — entrega registrada; protocolo não executado. SHA256:", digest)

def cmd_review(a):
    local, _ = config()
    data = task(a.id)
    target = {"aprovada": "aprovada", "ajustes": "ajustes", "reprovada": "reprovada"}[a.decisao]
    transition(data, target)
    data["revisao"] = {"decisao": a.decisao, "feedback": a.feedback, "por": local["colaborador"], "em": now()}
    event(data, "revisada", local["colaborador"], a.decisao)
    save(task_path(a.id), data)
    auto_git([f"fila/{a.id}.json"], f"fila: revisar {a.id}")
    print("OK — revisão registrada; aprovação não equivale a protocolo.")

def cmd_reopen(a):
    local, _ = config()
    data = task(a.id)
    if data.get("advogado") != local["colaborador"]:
        raise SystemExit("Assuma a tarefa antes de reabrir os ajustes.")
    transition(data, "em_execucao")
    event(data, "ajustes_iniciados", local["colaborador"])
    save(task_path(a.id), data)
    auto_git([f"fila/{a.id}.json"], f"fila: iniciar ajustes {a.id}")
    print("OK — ajustes iniciados.")

def cmd_propose(a):
    local, _ = config()
    data = task(a.id)
    if data["status"] != "aprovada":
        raise SystemExit("A proposta exige tarefa aprovada.")
    source = Path(a.arquivo).expanduser().resolve()
    if not source.is_file():
        raise SystemExit("Arquivo da proposta não encontrado.")
    content = source.read_text(encoding="utf-8")
    if data["cnj"] in content or data["referencia_entrada"].lower() in content.lower():
        raise SystemExit("A proposta contém identificador do caso; extraia apenas aprendizado reutilizável.")
    name = slug(a.nome)
    target = ROOT / "propostas" / f"{name}--{a.id}.md"
    header = f"---\nskill: {name}\ntarefa_origem: {a.id}\nproposta_por: {local['colaborador']}\nproposta_em: {now()}\n---\n\n"
    target.write_text(header + content, encoding="utf-8")
    auto_git([str(target.relative_to(ROOT))], f"skill: propor {name}")
    print("OK — proposta criada:", target.relative_to(ROOT))

def cmd_promote(a):
    local, _ = config()
    proposal = ROOT / "propostas" / a.proposta
    if not proposal.is_file() or proposal.suffix != ".md":
        raise SystemExit("Proposta não encontrada.")
    match = re.search(r"^skill:\s*(.+)$", proposal.read_text(encoding="utf-8"), re.M)
    if not match:
        raise SystemExit("Proposta sem nome de skill.")
    name = slug(match.group(1))
    target = ROOT / "skills" / name / "SKILL.md"
    if target.exists():
        raise SystemExit("Skill já existe; promoção não sobrescreve. Faça proposta de atualização revisável.")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = proposal.read_text(encoding="utf-8")
    target.write_text(f"---\nname: {name}\ndescription: Skill candidata promovida após revisão humana.\n---\n\n" + body, encoding="utf-8")
    auto_git([str(target.relative_to(ROOT))], f"skill: promover {name}")
    print("OK — skill candidata promovida por", local["colaborador"], ":", target.relative_to(ROOT))

def cmd_status(a):
    print(json.dumps(task(a.id), ensure_ascii=False, indent=2))

def cmd_sync(_a):
    if not (ROOT / ".git").exists():
        raise SystemExit("Este diretório ainda não é um clone Git; nada foi sincronizado.")
    configure_git_credentials()
    quiet = hidden_subprocess_kwargs()
    remotes = subprocess.run(["git", "remote"], cwd=ROOT, text=True, capture_output=True, check=True, **quiet).stdout.split()
    if not remotes:
        raise SystemExit("Nenhum remote configurado; trabalho local preservado, nada sincronizado.")
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=True, **quiet).stdout
    if dirty:
        raise SystemExit("Há alterações locais não commitadas. Preserve-as em commit antes de sincronizar.")
    pull = subprocess.run(["git", "pull", "--rebase"], cwd=ROOT, **quiet)
    if pull.returncode:
        raise SystemExit("Conflito ou falha no pull. Estado preservado; concilie sem apagar versões.")
    push = subprocess.run(["git", "push"], cwd=ROOT, **quiet)
    if push.returncode:
        raise SystemExit("Pull concluído, mas push falhou; não declare sincronização completa.")
    print("OK — pull e push concluídos no remote configurado.")

def link_skill(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() and target.resolve() == source.resolve():
        return "já ligada"
    if target.exists() or target.is_symlink():
        return "preservada (já existia)"
    if platform.system() == "Windows":
        junction = subprocess.run(["cmd", "/c", "mklink", "/J", str(target), str(source)],
                                  capture_output=True, text=True, **hidden_subprocess_kwargs())
        if junction.returncode == 0:
            return "ligada por junction"
        shutil.copytree(source, target)
        (target / ".copia-gerenciada").write_text(str(source), encoding="utf-8")
        return "copiada de forma gerenciada (junction indisponível)"
    target.symlink_to(source, target_is_directory=True)
    return "ligada"

def cmd_install_skills(a):
    base = Path(a.destino_base).expanduser().resolve() if a.destino_base else Path.home()
    results = []
    for source in sorted((ROOT / "skills").iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            continue
        for relative in (Path(".claude/skills"), Path(".agents/skills")):
            target = base / relative / source.name
            results.append((target, link_skill(source, target)))
    for target, status in results:
        print("OK —", status, ":", target)

def cmd_prepare_auto_sync(_a):
    runtime = ROOT / ".esteira-runtime"
    runtime.mkdir(exist_ok=True)
    runner = runtime / "auto-sync.py"
    runner.write_text("""#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
root = Path(__file__).resolve().parents[1]
log = Path(__file__).with_name('auto-sync.log')
def record(message):
    with log.open('a', encoding='utf-8') as f:
        f.write(datetime.now(timezone.utc).isoformat(timespec='seconds') + ' ' + message + '\\n')
quiet = {'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0)} if platform.system() == 'Windows' else {}
gh = shutil.which('gh')
if gh:
    subprocess.run([gh, 'auth', 'setup-git'], capture_output=True, **quiet)
dirty = subprocess.run(['git','status','--porcelain'], cwd=root, text=True, capture_output=True, **quiet)
if dirty.returncode or dirty.stdout:
    record('BLOQUEADO arvore suja ou Git indisponivel; nada alterado')
    raise SystemExit(0)
fetch = subprocess.run(['git','fetch','origin'], cwd=root, capture_output=True, **quiet)
if fetch.returncode:
    record('FALHA fetch; nada apagado')
    raise SystemExit(fetch.returncode)
pull = subprocess.run(['git','pull','--rebase'], cwd=root, capture_output=True, **quiet)
if pull.returncode:
    subprocess.run(['git','rebase','--abort'], cwd=root, capture_output=True, **quiet)
    record('CONFLITO preservado; rebase abortado para conciliacao')
    raise SystemExit(pull.returncode)
inbox = subprocess.run([sys.executable, str(Path(__file__).resolve().parent.parent / 'esteira.py'),
                        'checar-intimacoes', '--somente-se-dia-novo', '--silencioso'],
                       cwd=root, text=True, capture_output=True, **quiet)
if inbox.stdout.strip():
    record(inbox.stdout.strip())
elif inbox.returncode:
    record('INBOX Sync indisponivel; fila e estado remoto preservados')
push = subprocess.run(['git','push','origin','HEAD'], cwd=root, capture_output=True, **quiet)
record('OK sincronizado' if push.returncode == 0 else 'FALHA push; commits locais preservados')
raise SystemExit(push.returncode)
""", encoding="utf-8")
    os.chmod(runner, 0o700)
    python = Path(sys.executable).resolve()
    if platform.system() == "Windows":
        pythonw = python.with_name("pythonw.exe")
        if pythonw.exists():
            python = pythonw
        task = runtime / "INSTALAR-TAREFA-WINDOWS.ps1"
        task.write_text(f'''$Action = New-ScheduledTaskAction -Execute "{python}" -Argument '"{runner}"'\n$TriggerRepeticao = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)\n$TriggerEntrada = New-ScheduledTaskTrigger -AtLogOn\nRegister-ScheduledTask -TaskName "Kit3AutoSync" -Action $Action -Trigger @($TriggerRepeticao, $TriggerEntrada) -Description "Sincroniza o repositorio privado e consulta a caixa do Sync em leitura" -Force\n''', encoding="utf-8")
        print("OK — execute internamente e valide a tarefa:", task)
    else:
        plist = runtime / "com.marcuspeterson.kit3.autosync.plist"
        plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.marcuspeterson.kit3.autosync</string>
<key>ProgramArguments</key><array><string>{python}</string><string>{runner}</string></array>
<key>StartInterval</key><integer>600</integer>
<key>RunAtLoad</key><true/>
</dict></plist>
''', encoding="utf-8")
        print("OK — instale internamente no LaunchAgents e valide uma execução:", plist)

def _pedir_chave_sync():
    """Recebe o segredo sem colocá-lo em argumento, Git ou texto da conversa."""
    if os.getenv("KIT3_SYNC_KEY"):
        return os.environ["KIT3_SYNC_KEY"]
    if platform.system() == "Darwin":
        script = 'display dialog "Cole a chave do Sync" default answer "" with hidden answer buttons {"Cancelar", "Salvar"} default button "Salvar"\ntext returned of result'
        result = subprocess.run(["osascript", "-e", script], text=True, capture_output=True)
        if result.returncode:
            raise SystemExit("Configuração do Sync cancelada; nenhuma chave foi salva.")
        return result.stdout.rstrip("\n")
    if platform.system() == "Windows":
        command = "$c=Get-Credential -UserName 'SYNC' -Message 'Cole a chave do Sync no campo de senha'; $c.GetNetworkCredential().Password"
        result = subprocess.run(["powershell", "-NoProfile", "-Command", command], text=True, capture_output=True)
        if result.returncode:
            raise SystemExit("Configuração do Sync cancelada; nenhuma chave foi salva.")
        return result.stdout.rstrip("\r\n")
    return getpass.getpass("Chave do Sync (não será exibida): ")

def cmd_configure_sync(_a):
    local, shared = config()
    if not shared.get("conectores", {}).get("sync", {}).get("somente_leitura"):
        raise SystemExit("BLOQUEADO: o conector não está marcado como somente leitura.")
    chave, origem = sync_connector.descobrir_chave_existente(local["organizacao_id"])
    reutilizada = bool(chave)
    if not chave:
        chave = _pedir_chave_sync()
    cliente = sync_connector.ClienteSync(chave)
    try:
        conta = cliente.conta()
    except RuntimeError as exc:
        raise SystemExit(f"A chave não foi salva: {exc}")
    if not conta.get("ativo") or not conta.get("acesso_liberado"):
        raise SystemExit("A conta do Sync não está ativa/liberada; a chave não foi salva.")
    if not reutilizada:
        sync_connector.salvar_chave(chave, local["organizacao_id"])
    print("OK — Sync conectado em modo somente leitura para:", conta.get("conta") or "conta identificada")
    if reutilizada:
        print("OK — integração já existente reutilizada sem mover ou duplicar a chave:", origem)
    else:
        print("OK — chave guardada somente neste computador, fora do Git e da conversa.")

def cmd_test_sync(_a):
    local, _shared = config()
    try:
        conta = sync_connector.ClienteSync(sync_connector.carregar_chave(local["organizacao_id"])).conta()
    except RuntimeError as exc:
        raise SystemExit(f"FALHA — Sync: {exc}")
    print("OK — leitura do Sync autorizada para:", conta.get("conta") or "conta identificada")

def parser():
    p = argparse.ArgumentParser(description="Kit 3 — Esteira de Petições operada por uma pessoa só")
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("iniciar-escritorio"); q.add_argument("--nome", required=True); q.add_argument("--escritorio", required=True); q.add_argument("--agente", choices=sorted(VALID_AGENTS), default="claude"); q.add_argument("--repositorio", default=""); q.set_defaults(fn=cmd_start_office)
    q = sub.add_parser("configurar-documentos"); q.add_argument("--onde-modelos", required=True); q.add_argument("--pastas-clientes", choices=["sim", "nao"], required=True); q.add_argument("--destino-copia", required=True); q.add_argument("--padrao-nomes", required=True); q.add_argument("--caminho-local-modelos", default=""); q.add_argument("--caminho-local-clientes", default=""); q.set_defaults(fn=cmd_configure_documents)
    q = sub.add_parser("diagnosticar"); q.set_defaults(fn=cmd_diagnose)
    q = sub.add_parser("criar-tarefa"); q.add_argument("--cnj", required=True); q.add_argument("--referencia", required=True); q.add_argument("--providencia", required=True); q.set_defaults(fn=cmd_create)
    q = sub.add_parser("checar-intimacoes"); q.add_argument("--somente-se-dia-novo", action="store_true"); q.add_argument("--silencioso", action="store_true"); q.set_defaults(fn=cmd_check_intimations)
    q = sub.add_parser("importar-intimacao"); q.add_argument("id_sync", type=int); q.add_argument("--providencia", required=True); q.set_defaults(fn=cmd_import_intimation)
    q = sub.add_parser("listar"); q.add_argument("--status"); q.set_defaults(fn=cmd_list)
    q = sub.add_parser("atribuir"); q.add_argument("id"); q.add_argument("--providencia", default=""); q.add_argument("--responsavel", default=""); q.add_argument("--automatizar", action="store_true"); q.set_defaults(fn=cmd_assign)
    q = sub.add_parser("assumir"); q.add_argument("id"); q.set_defaults(fn=cmd_claim)
    q = sub.add_parser("contexto"); q.add_argument("id"); q.set_defaults(fn=cmd_context)
    q = sub.add_parser("entregar"); q.add_argument("id"); q.add_argument("arquivo"); q.add_argument("--modelo", required=True); q.add_argument("--copia-destino", required=True); q.set_defaults(fn=cmd_submit)
    q = sub.add_parser("revisar"); q.add_argument("id"); q.add_argument("decisao", choices=["aprovada", "ajustes", "reprovada"]); q.add_argument("--feedback", required=True); q.set_defaults(fn=cmd_review)
    q = sub.add_parser("iniciar-ajustes"); q.add_argument("id"); q.set_defaults(fn=cmd_reopen)
    q = sub.add_parser("propor-skill"); q.add_argument("id"); q.add_argument("--nome", required=True); q.add_argument("--arquivo", required=True); q.set_defaults(fn=cmd_propose)
    q = sub.add_parser("promover-skill"); q.add_argument("proposta"); q.set_defaults(fn=cmd_promote)
    q = sub.add_parser("status"); q.add_argument("id"); q.set_defaults(fn=cmd_status)
    q = sub.add_parser("sincronizar"); q.set_defaults(fn=cmd_sync)
    q = sub.add_parser("instalar-skills"); q.add_argument("--destino-base"); q.set_defaults(fn=cmd_install_skills)
    q = sub.add_parser("preparar-auto-sync"); q.set_defaults(fn=cmd_prepare_auto_sync)
    q = sub.add_parser("configurar-sync"); q.set_defaults(fn=cmd_configure_sync)
    q = sub.add_parser("testar-sync"); q.set_defaults(fn=cmd_test_sync)
    return p

if __name__ == "__main__":
    args = parser().parse_args()
    try:
        args.fn(args)
    except KeyboardInterrupt:
        raise SystemExit("Interrompido; estado anterior preservado.")

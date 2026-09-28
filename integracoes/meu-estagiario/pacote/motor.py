#!/usr/bin/env python3
"""Motor opcional e agendado: fecha o ciclo direto no Meu Estagiário, para quem opera sozinho.

Kit 3 parte de uma pessoa só no Claude Code (o Dono, que acumula todos os papéis e é sempre quem
opera a esteira) com o Meu Estagiário como única interface para o resto da equipe. Sem o motor, o
espelhamento (`ponte.py`) é sempre manual, um comando por vez. Com o motor instalado (agendado,
mesmo padrão do auto-sync do núcleo): você escreve uma nota num card já espelhado dizendo o que
fazer; o motor lê essa nota, registra a providência na fila, e na mesma passada dispara headless a
mesma skill que você rodaria (/resumo-do-processo + /gerar-peticao-por-modelo), devolvendo o link
da minuta como nota na mesma tarefa.

"Quem opera o Kit" (sempre você/a esteira) e "quem deve receber o card no Meu Estagiário" (pode ser
qualquer pessoa real do escritório, sem Claude Code nenhum) são coisas diferentes. Por padrão o card
fica com você; a nota pode incluir uma linha `Responsável: <nome exato>` para direcioná-lo a outra
pessoa do time — o motor só aceita nome que bate exatamente com um cadastro real no Meu Estagiário.

Gates preservados: nunca protocola, nunca nasce de documento vazio, nunca escreve financeiro nem
sobrescreve skill do Meu Estagiário. Se não concluir sozinho, avisa e pede continuação humana em
vez de tentar de novo ou falhar em silêncio.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import instalar  # noqa: E402
import ponte  # noqa: E402

MARCADOR_ROBO = "[ESTEIRA]"
ESTADO_PATH_REL = Path(".esteira-runtime/integracoes/meu-estagiario/motor-estado.json")


class MotorError(RuntimeError):
    pass


def hidden_subprocess_kwargs() -> dict[str, Any]:
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if platform.system() == "Windows" else {}


def local_config(kit_root: Path) -> dict[str, Any]:
    caminho = kit_root / ".escritorio.local.json"
    if not caminho.is_file():
        raise MotorError("Configuração local do Kit ausente; instale o núcleo antes do motor.")
    return json.loads(caminho.read_text(encoding="utf-8"))


def integracao_habilitada(local: dict[str, Any]) -> bool:
    return bool((local.get("integracoes") or {}).get("meu_estagiario", {}).get("habilitado"))


def carregar_estado(kit_root: Path) -> dict[str, Any]:
    caminho = kit_root / ESTADO_PATH_REL
    if not caminho.is_file():
        return {"schema_version": 1, "tarefas": {}}
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar_estado(kit_root: Path, estado: dict[str, Any]) -> None:
    caminho = kit_root / ESTADO_PATH_REL
    caminho.parent.mkdir(parents=True, exist_ok=True)
    tmp = caminho.with_suffix(".tmp")
    tmp.write_text(json.dumps(estado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, caminho)


def id_da_tarefa_kit(descricao: str) -> str | None:
    match = re.search(r"\[KIT3_TAREFA:([^\]]+)\]", descricao or "")
    return match.group(1) if match else None


def parse_nota(texto: str) -> dict[str, Any]:
    """A nota vira providência. Uma linha "Responsável: <nome>" é opcional — sem ela, o card fica
    com você (comportamento padrão, escritório de uma pessoa só)."""
    if re.match(r"(?i)^\s*n[ãa]o\s+automatizar\b", texto or ""):
        return {"automatizar": False, "providencia": (texto or "").strip(), "responsavel": ""}
    responsavel = ""
    resto: list[str] = []
    for linha in (texto or "").splitlines():
        bruta = linha.strip()
        m_resp = re.match(r"(?i)^respons[aá]vel\s*:\s*(.+)$", bruta)
        if m_resp:
            responsavel = m_resp.group(1).strip()
        elif bruta:
            resto.append(bruta)
    providencia = " ".join(resto) if resto else (texto or "").strip()
    return {"automatizar": True, "providencia": providencia, "responsavel": responsavel}


def listar_tarefas_kit_no_me(api: instalar.API) -> list[dict[str, Any]]:
    todas = ponte.paged(api, "/tarefas?incluir_arquivadas=false", "tarefas")
    return [t for t in todas if id_da_tarefa_kit(str(t.get("descricao") or ""))]


def notas_da_tarefa(api: instalar.API, me_task_id: str) -> list[dict[str, Any]]:
    detalhe = api.get(f"/tarefas/{me_task_id}").get("tarefa", {})
    return sorted(detalhe.get("notas") or [], key=lambda n: str(n.get("criada_em") or n.get("data") or ""))


def postar_nota(api: instalar.API, me_task_id: str, texto: str) -> None:
    corpo = f"{MARCADOR_ROBO} {texto}"
    if len(corpo) > 3000:
        corpo = corpo[:2950] + "… (mensagem truncada pela política de 3000 caracteres do escritório)"
    api.post(f"/tarefas/{me_task_id}/notas", {"texto": corpo})


def executar_esteira(kit_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(kit_root / "esteira.py"), *args],
        cwd=kit_root, text=True, capture_output=True, **hidden_subprocess_kwargs(),
    )


def montar_prompt_headless(kit_id: str) -> str:
    return (
        f"Você está no clone privado do Kit 3. Rode `python3 esteira.py contexto {kit_id}` se ainda "
        f"não tiver rodado, aplique integralmente /resumo-do-processo e depois "
        f"/gerar-peticao-por-modelo para produzir a minuta da tarefa {kit_id} "
        f"(fila/{kit_id}.json), sempre a partir de cópia de modelo aprovado — nunca documento "
        f"vazio. Se faltar modelo, autos determinantes ou qualquer dado necessário, PARE, "
        f"registre a lacuna e não finja concluir. Se e somente se concluir de verdade, rode "
        f"`python3 esteira.py entregar {kit_id} ARQUIVO --modelo IDENTIFICAÇÃO --copia-destino DESTINO` "
        f"com os valores reais. Não protocole nada. Não use casos de teste."
    )


def rodar_claude_headless(kit_root: Path, prompt: str, executor=None) -> subprocess.CompletedProcess:
    """Isolado numa função própria para poder ser trocado em teste — é o trecho do motor ainda sem
    prova de campo. Primeira execução real deve ser acompanhada."""
    if executor is not None:
        return executor(kit_root, prompt)
    binario = shutil.which("claude")
    if not binario:
        raise MotorError("CLI do Claude Code não encontrada no PATH desta máquina.")
    return subprocess.run(
        [binario, "-p", prompt, "--permission-mode", "acceptEdits"],
        cwd=kit_root, text=True, capture_output=True, timeout=1800, **hidden_subprocess_kwargs(),
    )


def processar_tarefa(api: instalar.API, kit_root: Path, kit_id: str, me_id: str,
                      providencia: str, responsavel: str = "", executor=None) -> str:
    """Registra providência (e responsável, se dado), tenta produzir a minuta na mesma passada.
    Devolve 1 linha de log."""
    args = ["atribuir", kit_id, "--providencia", providencia, "--automatizar"]
    if responsavel:
        args += ["--responsavel", responsavel]
    atribuir = executar_esteira(kit_root, *args)
    if atribuir.returncode != 0:
        postar_nota(api, me_id, f"Não consegui registrar a providência: "
                                 f"{(atribuir.stderr or atribuir.stdout).strip()[:400]}")
        return f"{kit_id}: falhou ao registrar providência."
    if responsavel:
        # O card muda de dono no Meu Estagiário na hora, mesmo antes da minuta ficar pronta.
        tarefa_atribuida = json.loads((kit_root / "fila" / f"{kit_id}.json").read_text(encoding="utf-8"))
        members = ponte.paged(api, "/membros", "membros")
        ponte.mirror(api, tarefa_atribuida, members)
    assumir = executar_esteira(kit_root, "assumir", kit_id)
    if assumir.returncode != 0:
        postar_nota(api, me_id, f"Não consegui assumir a tarefa: {assumir.stderr.strip()[:400]}")
        return f"{kit_id}: falhou ao assumir."
    contexto = executar_esteira(kit_root, "contexto", kit_id)
    if contexto.returncode != 0:
        postar_nota(api, me_id, "O Sync não liberou os autos agora. Tentando de novo no próximo "
                                 f"ciclo. Detalhe: {contexto.stderr.strip()[:300]}")
        return f"{kit_id}: Sync não liberou os autos."
    resultado_claude = rodar_claude_headless(kit_root, montar_prompt_headless(kit_id), executor)
    atual = json.loads((kit_root / "fila" / f"{kit_id}.json").read_text(encoding="utf-8"))
    if atual.get("status") == "entregue":
        entrega = atual.get("entrega") or {}
        members = ponte.paged(api, "/membros", "membros")
        ponte.mirror(api, atual, members)
        postar_nota(api, me_id, "Minuta gerada e entregue para revisão. "
                                 f"Modelo: {entrega.get('modelo_utilizado')}. "
                                 f"Destino da cópia: {entrega.get('copia_destino')}. "
                                 "Protocolo continua manual, revisão obrigatória antes disso.")
        return f"{kit_id}: entregue e avisado no Meu Estagiário."
    trecho = (resultado_claude.stdout or resultado_claude.stderr or "")[-500:]
    postar_nota(api, me_id, "Não concluí a minuta sozinho (ficou em execução). Abra uma conversa "
                             f"com o Claude nesta máquina e continue a tarefa {kit_id} — "
                             f"provavelmente falta modelo, autos ou uma decisão sua. "
                             f"Últimas linhas: {trecho}")
    return f"{kit_id}: não concluiu sozinho; card avisado para continuação humana."


PROVIDENCIA_AGUARDANDO_TRIAGEM = (
    "Aguardando decisão — leia os autos e responda com uma nota aqui dizendo o que fazer."
)


def _kit_id_da_intimacao(kit_root: Path, intimacao_id) -> str | None:
    for path in (kit_root / "fila").glob("*.json"):
        dados = json.loads(path.read_text(encoding="utf-8"))
        if str(dados.get("intimacao_sync_id") or "") == str(intimacao_id):
            return dados["id"]
    return None


def ciclo_captacao(api: instalar.API, kit_root: Path) -> list[str]:
    """Transforma intimação nova do Sync (já em cache local, atualizada 1x/dia pelo auto-sync do
    núcleo) em tarefa + card no Meu Estagiário, sem esperar ninguém abrir o Claude. A decisão
    continua sendo humana — só que ela acontece depois, dentro do Meu Estagiário, por nota."""
    inbox_path = kit_root / ".intimacoes-inbox" / "intimacoes.json"
    if not inbox_path.is_file():
        return []
    inbox = json.loads(inbox_path.read_text(encoding="utf-8"))
    relatorio: list[str] = []
    for item in inbox.get("intimacoes", {}).values():
        if item.get("importada_em"):
            continue
        resultado = executar_esteira(kit_root, "importar-intimacao", str(item["id"]),
                                      "--providencia", PROVIDENCIA_AGUARDANDO_TRIAGEM)
        if resultado.returncode != 0:
            relatorio.append(f"intimação {item['id']}: não virou tarefa — "
                              f"{resultado.stderr.strip()[:200]}")
            continue
        kit_id = _kit_id_da_intimacao(kit_root, item["id"])
        if not kit_id:
            relatorio.append(f"intimação {item['id']}: tarefa criada mas não localizada — ignorada.")
            continue
        tarefa = json.loads((kit_root / "fila" / f"{kit_id}.json").read_text(encoding="utf-8"))
        members = ponte.paged(api, "/membros", "membros")
        ponte.mirror(api, tarefa, members)
        relatorio.append(f"{kit_id}: intimação nova virou card no Meu Estagiário, aguardando sua nota.")
    return relatorio


def ciclo(kit_root: Path, executor=None, api: instalar.API | None = None) -> list[str]:
    local = local_config(kit_root)
    if not integracao_habilitada(local):
        raise MotorError("Integração com o Meu Estagiário ainda não foi instalada/habilitada.")
    if api is None:
        if not os.getenv(instalar.MANIFEST["credential_env"]):
            # Um agendamento não tem terminal: nunca deixar cair no getpass() do instalar.py e travar.
            raise MotorError(f"Variável {instalar.MANIFEST['credential_env']} ausente no ambiente "
                              f"deste agendamento; configure-a de forma permanente antes de "
                              f"instalar o motor.")
        api = instalar.API(instalar.token_from_environment())
    estado = carregar_estado(kit_root)
    tarefas_estado = estado.setdefault("tarefas", {})
    relatorio: list[str] = list(ciclo_captacao(api, kit_root))
    for me_task in listar_tarefas_kit_no_me(api):
        me_id = str(me_task["id"])
        kit_id = id_da_tarefa_kit(str(me_task.get("descricao") or ""))
        registro = tarefas_estado.setdefault(me_id, {"ultima_nota_em": ""})
        fila_path = kit_root / "fila" / f"{kit_id}.json"
        if not fila_path.is_file():
            relatorio.append(f"{me_id}: tarefa do Kit {kit_id} não existe mais localmente — ignorada.")
            continue
        tarefa_kit = json.loads(fila_path.read_text(encoding="utf-8"))
        if tarefa_kit.get("status") != "aberta":
            continue
        for nota in notas_da_tarefa(api, me_id):
            texto = str(nota.get("texto") or "")
            criada_em = str(nota.get("criada_em") or nota.get("data") or "")
            if texto.startswith(MARCADOR_ROBO):
                continue
            if criada_em and criada_em <= registro["ultima_nota_em"]:
                continue
            registro["ultima_nota_em"] = max(registro["ultima_nota_em"], criada_em)
            info = parse_nota(texto)
            if not info["automatizar"]:
                postar_nota(api, me_id, "Ok, não vou automatizar esta — cuido dela manualmente.")
                relatorio.append(f"{kit_id}: opt-out, segue manual.")
                break
            if not info["providencia"]:
                continue
            responsavel_resolvido = ""
            if info["responsavel"]:
                members = ponte.paged(api, "/membros", "membros")
                membro_id = ponte.exact_member(members, info["responsavel"])
                if not membro_id:
                    postar_nota(api, me_id, f"Não achei exatamente um membro chamado "
                                             f"\"{info['responsavel']}\" no Meu Estagiário. Confira "
                                             f"o nome e responda de novo com o nome exato.")
                    relatorio.append(f"{kit_id}: responsável não identificado — aguardando correção.")
                    break
                responsavel_resolvido = info["responsavel"]
            relatorio.append(processar_tarefa(api, kit_root, kit_id, me_id, info["providencia"],
                                               responsavel_resolvido, executor))
            break  # a tarefa mudou de status nesta passada; a próxima nota (se houver) espera o próximo ciclo
    salvar_estado(kit_root, estado)
    return relatorio


def instalar_agendamento(kit_root: Path) -> Path:
    runtime = kit_root / ".esteira-runtime" / "integracoes" / "meu-estagiario"
    runtime.mkdir(parents=True, exist_ok=True)
    runner = runtime / "motor-runner.py"
    runner.write_text("""#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
# Este arquivo mora em <kit_root>/.esteira-runtime/integracoes/meu-estagiario/motor-runner.py
kit_root = Path(__file__).resolve().parents[3]
motor = kit_root / 'integracoes' / 'meu-estagiario' / 'pacote' / 'motor.py'
log = Path(__file__).with_name('motor-runner.log')
def record(message):
    with log.open('a', encoding='utf-8') as f:
        f.write(datetime.now(timezone.utc).isoformat(timespec='seconds') + ' ' + message + '\\n')
resultado = subprocess.run([sys.executable, str(motor), 'ciclo', '--kit-root', str(kit_root)],
                           capture_output=True, text=True)
record(('OK ' if resultado.returncode == 0 else 'FALHA ') + (resultado.stdout or resultado.stderr).strip()[:2000])
""", encoding="utf-8")
    os.chmod(runner, 0o700)
    python = Path(sys.executable).resolve()
    if platform.system() == "Windows":
        pythonw = python.with_name("pythonw.exe")
        if pythonw.exists():
            python = pythonw
        tarefa = runtime / "INSTALAR-TAREFA-MOTOR-WINDOWS.ps1"
        tarefa.write_text(
            f'$Action = New-ScheduledTaskAction -Execute "{python}" -Argument \'"{runner}"\'\n'
            f'$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) '
            f'-RepetitionInterval (New-TimeSpan -Minutes 10)\n'
            f'Register-ScheduledTask -TaskName "Kit3MotorMeuEstagiario" -Action $Action '
            f'-Trigger $Trigger -Description "Le notas novas e roda a esteira sob demanda no Meu '
            f'Estagiario" -Force\n', encoding="utf-8")
        return tarefa
    plist = runtime / "com.marcuspeterson.kit3.motor-me.plist"
    plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.marcuspeterson.kit3.motor-me</string>
<key>ProgramArguments</key><array><string>{python}</string><string>{runner}</string></array>
<key>StartInterval</key><integer>600</integer>
<key>RunAtLoad</key><false/>
</dict></plist>
''', encoding="utf-8")
    return plist


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("ciclo"); c.add_argument("--kit-root", type=Path, required=True)
    i = sub.add_parser("instalar-agendamento"); i.add_argument("--kit-root", type=Path, required=True)
    args = p.parse_args()
    kit_root = args.kit_root.resolve()
    if args.cmd == "ciclo":
        saida = ciclo(kit_root)
        print(json.dumps(saida, ensure_ascii=False, indent=2))
    elif args.cmd == "instalar-agendamento":
        caminho = instalar_agendamento(kit_root)
        print("OK — instale internamente e valide uma execução:", caminho)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except MotorError as exc:
        raise SystemExit(f"MOTOR NÃO CONCLUÍDO — {exc}")

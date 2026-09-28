#!/usr/bin/env python3
"""Motor opcional e sob demanda-agendada: fecha o ciclo entre o Meu Estagiário e o Kit 3.

Este módulo NÃO é a esteira completa do Marcus (Sync -> Painel -> Monitor próprio). É a versão que
um escritório usando só o Meu Estagiário consegue rodar: o Controller responde a intimação por uma
nota no card já espelhado; o motor lê essa nota, atribui o responsável na fila do Kit e, na máquina
do Advogado, dispara headless a mesma skill que um humano rodaria (/resumo-do-processo +
/gerar-peticao-por-modelo) e devolve o link da minuta como nota. Cada ciclo é uma passada única,
pensada para ser chamada pelo mesmo agendamento do sistema operacional que já existe no Kit
(com.metodoeuro.autosync / MetodoEuroAutoSync) — não é um processo contínuo (daemon).

Gates preservados em toda a cadeia: nunca protocola, nunca nasce de documento vazio, nunca inventa
responsável por nome parecido (só por correspondência exata contra /membros), nunca escreve em
financeiro nem sobrescreve skill do Meu Estagiário, e todo passo que não concluir sozinho vira nota
pedindo continuação humana em vez de falhar em silêncio.
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

MARCADOR_ROBO = "[ESTEIRA-EURO]"
ESTADO_PATH_REL = Path(".metodo-euro-runtime/integracoes/meu-estagiario/motor-estado.json")


class MotorError(RuntimeError):
    pass


def hidden_subprocess_kwargs() -> dict[str, Any]:
    return {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)} if platform.system() == "Windows" else {}


def carregar_euro(kit_root: Path):
    """Importa o euro.py do clone do escritório (fora deste pacote) por caminho, sem duplicar lógica."""
    caminho = kit_root / "euro.py"
    if not caminho.is_file():
        raise MotorError("euro.py não encontrado no --kit-root informado; confirme o caminho do clone.")
    spec = importlib.util.spec_from_file_location("euro_kit", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(kit_root))
    try:
        spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    finally:
        sys.path.pop(0)
    return modulo


def local_config(kit_root: Path) -> dict[str, Any]:
    caminho = kit_root / ".metodo-euro.local.json"
    if not caminho.is_file():
        raise MotorError("Configuração local do Kit ausente; instale o núcleo antes do motor.")
    return json.loads(caminho.read_text(encoding="utf-8"))


def papeis_locais(local: dict[str, Any]) -> set[str]:
    return set(local.get("papeis") or [local.get("papel")]) - {None}


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
    match = re.search(r"\[METODO_EURO_ID:([^\]]+)\]", descricao or "")
    return match.group(1) if match else None


def parse_nota(texto: str) -> dict[str, str]:
    """Extrai Responsável/Providência de uma nota livre do Controller. Resto vira contexto."""
    resultado = {"responsavel": "", "providencia": "", "automatizar": True, "resto": []}
    for linha in (texto or "").splitlines():
        bruta = linha.strip()
        m_resp = re.match(r"(?i)^respons[aá]vel\s*:\s*(.+)$", bruta)
        m_prov = re.match(r"(?i)^provid[eê]ncia\s*:\s*(.+)$", bruta)
        if m_resp:
            resultado["responsavel"] = m_resp.group(1).strip()
        elif m_prov:
            resultado["providencia"] = m_prov.group(1).strip()
        elif re.match(r"(?i)^n[ãa]o\s+automatizar\b", bruta):
            resultado["automatizar"] = False
        elif bruta:
            resultado["resto"].append(bruta)
    if not resultado["providencia"] and resultado["resto"]:
        resultado["providencia"] = " ".join(resultado["resto"])
    return resultado


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


def executar_euro(kit_root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(kit_root / "euro.py"), *args],
        cwd=kit_root, text=True, capture_output=True, **hidden_subprocess_kwargs(),
    )


def ciclo_controller(api: instalar.API, kit_root: Path, local: dict[str, Any],
                      members: list[dict[str, Any]]) -> list[str]:
    """Lê notas humanas novas em cards espelhados e atribui responsável/providência na fila do Kit."""
    relatorio: list[str] = []
    estado = carregar_estado(kit_root)
    tarefas_estado = estado.setdefault("tarefas", {})
    for me_task in listar_tarefas_kit_no_me(api):
        me_id = str(me_task["id"])
        kit_id = id_da_tarefa_kit(str(me_task.get("descricao") or ""))
        registro = tarefas_estado.setdefault(me_id, {"ultima_nota_em": "", "avisadas": []})
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
            nota_id = str(nota.get("id") or criada_em)
            if texto.startswith(MARCADOR_ROBO):
                continue
            if criada_em and criada_em <= registro["ultima_nota_em"]:
                continue
            info = parse_nota(texto)
            if not info["responsavel"]:
                if nota_id not in registro["avisadas"]:
                    postar_nota(api, me_id, "Não encontrei uma linha \"Responsável: <nome>\" nesta nota. "
                                             "Responda com o nome exatamente como aparece no Meu Estagiário.")
                    registro["avisadas"].append(nota_id)
                registro["ultima_nota_em"] = max(registro["ultima_nota_em"], criada_em)
                continue
            responsavel_id = ponte.exact_member(members, info["responsavel"])
            if not responsavel_id:
                if nota_id not in registro["avisadas"]:
                    postar_nota(api, me_id, f"Não achei exatamente um membro chamado "
                                             f"\"{info['responsavel']}\". Confira o nome em /membros e "
                                             f"escreva de novo com o nome exato.")
                    registro["avisadas"].append(nota_id)
                registro["ultima_nota_em"] = max(registro["ultima_nota_em"], criada_em)
                continue
            args = ["atribuir", kit_id, "--responsavel", info["responsavel"]]
            if info["providencia"]:
                args += ["--providencia", info["providencia"]]
            if info["automatizar"]:
                args.append("--automatizar")
            resultado = executar_euro(kit_root, *args)
            if resultado.returncode != 0:
                postar_nota(api, me_id, f"Não consegui atribuir automaticamente: "
                                         f"{(resultado.stderr or resultado.stdout).strip()[:400]}")
            else:
                relatorio.append(f"{me_id}: atribuída a {info['responsavel']} (tarefa {kit_id}).")
                postar_nota(api, me_id, f"Atribuída a {info['responsavel']}. "
                                         f"O Advogado vai receber isso na fila normalmente.")
            registro["ultima_nota_em"] = max(registro["ultima_nota_em"], criada_em)
    salvar_estado(kit_root, estado)
    return relatorio


def montar_prompt_headless(kit_id: str) -> str:
    return (
        f"Você está no clone privado do Kit 3 - Implementando sua Esteira de Petições Automatizadas. "
        f"Assuma o papel de Advogado para a tarefa {kit_id} da fila (fila/{kit_id}.json). "
        f"Rode `python3 euro.py contexto {kit_id}` se ainda não tiver rodado, aplique integralmente "
        f"/resumo-do-processo e depois /gerar-peticao-por-modelo para produzir a minuta, sempre a "
        f"partir de cópia de modelo aprovado — nunca documento vazio. Se faltar modelo, autos "
        f"determinantes ou qualquer dado necessário, PARE, registre a lacuna e não finja concluir. "
        f"Se e somente se concluir de verdade, rode "
        f"`python3 euro.py entregar {kit_id} ARQUIVO --modelo IDENTIFICAÇÃO --copia-destino DESTINO` "
        f"com os valores reais. Não protocole nada. Não use casos de teste."
    )


def rodar_claude_headless(kit_root: Path, prompt: str, executor=None) -> subprocess.CompletedProcess:
    """Isolado numa função própria para poder ser trocado em teste — é o único trecho do motor que
    ainda não tem prova de campo em escritório de aluno. Primeira execução real deve ser acompanhada."""
    if executor is not None:
        return executor(kit_root, prompt)
    binario = shutil.which("claude")
    if not binario:
        raise MotorError("CLI do Claude Code não encontrada no PATH desta máquina.")
    return subprocess.run(
        [binario, "-p", prompt, "--permission-mode", "acceptEdits"],
        cwd=kit_root, text=True, capture_output=True, timeout=1800, **hidden_subprocess_kwargs(),
    )


def ciclo_advogado(api: instalar.API, kit_root: Path, local: dict[str, Any],
                    executor=None) -> list[str]:
    """Para tarefas abertas, atribuídas ao colaborador local e marcadas automatizar=true, dispara
    headless a mesma skill que um humano rodaria, e devolve o resultado como nota no Meu Estagiário."""
    relatorio: list[str] = []
    colaborador = local.get("colaborador")
    for path in sorted((kit_root / "fila").glob("*.json")):
        tarefa = json.loads(path.read_text(encoding="utf-8"))
        if tarefa.get("status") != "aberta" or not tarefa.get("automatizar"):
            continue
        if tarefa.get("responsavel") != colaborador:
            continue
        kit_id = tarefa["id"]
        assumir = executar_euro(kit_root, "assumir", kit_id)
        if assumir.returncode != 0:
            relatorio.append(f"{kit_id}: não consegui assumir — {assumir.stderr.strip()[:300]}")
            continue
        contexto = executar_euro(kit_root, "contexto", kit_id)
        if contexto.returncode != 0:
            relatorio.append(f"{kit_id}: Sync não liberou os autos — {contexto.stderr.strip()[:300]}")
            continue
        resultado_claude = rodar_claude_headless(kit_root, montar_prompt_headless(kit_id), executor)
        atual = json.loads((kit_root / "fila" / f"{kit_id}.json").read_text(encoding="utf-8"))
        me_task = ponte.find_existing(api, kit_id)
        if not me_task:
            relatorio.append(f"{kit_id}: sem card espelhado no Meu Estagiário para avisar o resultado.")
            continue
        me_id = str(me_task["id"])
        if atual.get("status") == "entregue":
            entrega = atual.get("entrega") or {}
            ponte.mirror(api, atual, ponte.paged(api, "/membros", "membros"))
            postar_nota(api, me_id, "Minuta gerada e entregue para revisão. "
                                     f"Modelo: {entrega.get('modelo_utilizado')}. "
                                     f"Destino da cópia: {entrega.get('copia_destino')}. "
                                     "Protocolo continua manual, revisão humana obrigatória antes disso.")
            relatorio.append(f"{kit_id}: entregue e avisado no Meu Estagiário.")
        else:
            trecho = (resultado_claude.stdout or resultado_claude.stderr or "")[-500:]
            postar_nota(api, me_id, "Não concluí a minuta sozinho (ficou em execução). "
                                     "Abra uma conversa com o Claude nesta máquina e continue a tarefa "
                                     f"{kit_id} — provavelmente falta modelo, autos ou uma decisão sua. "
                                     f"Últimas linhas: {trecho}")
            relatorio.append(f"{kit_id}: não concluiu sozinho; card avisado para continuação humana.")
    return relatorio


def ciclo(kit_root: Path, executor=None) -> dict[str, Any]:
    local = local_config(kit_root)
    if not integracao_habilitada(local):
        raise MotorError("Integração com o Meu Estagiário ainda não foi instalada/habilitada.")
    if not os.getenv(instalar.MANIFEST["credential_env"]):
        # Um agendamento não tem terminal: nunca deixar cair no getpass() do instalar.py e travar.
        raise MotorError(f"Variável {instalar.MANIFEST['credential_env']} ausente no ambiente deste "
                          f"agendamento; configure-a de forma permanente antes de instalar o motor.")
    api = instalar.API(instalar.token_from_environment())
    papeis = papeis_locais(local)
    saida: dict[str, Any] = {"controller": [], "advogado": []}
    if "controller" in papeis:
        members = ponte.paged(api, "/membros", "membros")
        saida["controller"] = ciclo_controller(api, kit_root, local, members)
    if "advogado" in papeis:
        saida["advogado"] = ciclo_advogado(api, kit_root, local, executor)
    return saida


def instalar_agendamento(kit_root: Path) -> Path:
    runtime = kit_root / ".metodo-euro-runtime" / "integracoes" / "meu-estagiario"
    runtime.mkdir(parents=True, exist_ok=True)
    runner = runtime / "motor-runner.py"
    runner.write_text("""#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
# Este arquivo mora em <kit_root>/.metodo-euro-runtime/integracoes/meu-estagiario/motor-runner.py
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
            f'Register-ScheduledTask -TaskName "MetodoEuroMotorMeuEstagiario" -Action $Action '
            f'-Trigger $Trigger -Description "Le notas novas e roda a esteira sob demanda no Meu '
            f'Estagiario" -Force\n', encoding="utf-8")
        return tarefa
    plist = runtime / "com.metodoeuro.motor-me.plist"
    plist.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.metodoeuro.motor-me</string>
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

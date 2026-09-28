#!/usr/bin/env python3
"""Instalador híbrido (API + interface) da Esteira no ADVBOX do aluno."""
from __future__ import annotations

import argparse, getpass, hashlib, json, os, shutil, ssl, subprocess, tempfile, unicodedata
import urllib.error, urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifesto.json").read_text(encoding="utf-8"))

class InstallError(RuntimeError): pass

def now() -> str: return datetime.now(timezone.utc).isoformat(timespec="seconds")
def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).casefold().split())

def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    try: os.chmod(path, 0o600)
    except OSError: pass

class API:
    def __init__(self, token: str, *, allow_task_creation: bool = False,
                 base: str = MANIFEST["api_base"], timeout: int = 30):
        self.token, self.base, self.timeout = token.strip(), base.rstrip("/"), timeout
        self.allow_task_creation = allow_task_creation

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        if method != "GET" and not (method == "POST" and path == "/posts" and self.allow_task_creation):
            raise InstallError("O conector só permite leitura e criação controlada de tarefas em /posts.")
        url = self.base + path; data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bear" + f"er {self.token}", "Accept": "application/json",
            "Content-Type": "application/json", "User-Agent": "Metodo-Euro-ADVBOX-Installer/1.1"})
        try:
            try:
                import certifi  # type: ignore
                context = ssl.create_default_context(cafile=certifi.where())
            except ImportError: context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=self.timeout, context=context) as res:
                raw = res.read(); return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:800]
            raise InstallError(f"ADVBOX respondeu HTTP {exc.code} em {method} {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc) and shutil.which("curl"): return self._curl(method, url, body)
            raise InstallError(f"Falha de rede na ADVBOX: {exc}") from exc

    def _curl(self, method: str, url: str, body: dict[str, Any] | None) -> Any:
        header = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8"); payload = None
        try:
            os.chmod(header.name, 0o600)
            header.write("Authorization: Bear" + f"er {self.token}\nAccept: application/json\nContent-Type: application/json\n"); header.close()
            cmd = ["curl", "-sS", "--fail-with-body", "-A", "Metodo-Euro-ADVBOX-Installer/1.1",
                   "-X", method, "-H", f"@{header.name}", "--max-time", str(self.timeout)]
            if body is not None:
                payload = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
                os.chmod(payload.name, 0o600); json.dump(body, payload, ensure_ascii=False); payload.close()
                cmd += ["--data-binary", f"@{payload.name}"]
            cmd.append(url); done = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
            if done.returncode: raise InstallError(f"ADVBOX recusou {method}: {(done.stderr or done.stdout)[:800]}")
            return json.loads(done.stdout) if done.stdout.strip() else {}
        finally:
            Path(header.name).unlink(missing_ok=True)
            if payload: Path(payload.name).unlink(missing_ok=True)

    def get(self, path: str) -> Any: return self.request("GET", path)
    def post_task(self, body: dict[str, Any]) -> Any: return self.request("POST", "/posts", body)

def token_from_environment() -> str:
    token = os.getenv(MANIFEST["credential_env"], "").strip()
    return token or getpass.getpass("Chave da ADVBOX (não será exibida): ").strip()

def audit(api: API) -> dict[str, Any]:
    settings = api.get("/settings")
    if not {"users", "tasks", "stages"}.issubset(settings): raise InstallError("GET /settings não devolveu os catálogos mínimos.")
    catalog = settings.get("tasks", []); mapping, missing = {}, []
    for spec in MANIFEST["task_types"]:
        matches = [item for item in catalog if norm(item.get("task")) == norm(spec["name"])]
        if len(matches) == 1: mapping[spec["key"]] = matches[0].get("id")
        elif not matches: missing.append(spec["name"])
        else: raise InstallError(f"Há tipos de tarefa duplicados na ADVBOX: {spec['name']}")
    return {"settings": settings, "task_mapping": mapping, "missing_task_types": missing}

def evidence(path: Path | None) -> dict[str, Any] | None:
    if not path: return None
    if not path.is_file(): raise InstallError("A evidência visual da configuração não foi encontrada.")
    return {"file": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

def configure_kit(kit_root: Path, data: dict[str, Any], ui_evidence: dict[str, Any]) -> Path:
    path = kit_root / ".metodo-euro.local.json"
    if not path.is_file(): raise InstallError("Instale primeiro o núcleo do Kit 3 no clone privado.")
    local = json.loads(path.read_text(encoding="utf-8"))
    if local.get("repositorio_privado_confirmado") is not True: raise InstallError("O repositório privado ainda não foi confirmado.")
    local.setdefault("integracoes", {})["advbox"] = {
        "habilitado": True, "modo": MANIFEST["mode"], "fila_operacional": "advbox",
        "fonte_autos": "sync_somente_leitura", "api_base": MANIFEST["api_base"],
        "credencial": {"variavel": MANIFEST["credential_env"]}, "task_mapping": data["task_mapping"],
        "evidencia_interface": ui_evidence, "configurado_em": now()}
    atomic_json(path, local); return path

def test_task(api: API, data: dict[str, Any], lawsuit_id: str, user_id: str) -> dict[str, Any]:
    task_type = data["task_mapping"].get("entrada")
    if not task_type: raise InstallError("O tipo [EURO] VALIDAR ENTRADA ainda não existe.")
    body = {"from": user_id, "guests": [user_id], "tasks_id": task_type, "lawsuits_id": lawsuit_id,
            "start_date": date.today().isoformat(),
            "comments": "[TESTE MÉTODO EURO] Validar integração; concluir manualmente após conferência."}
    created = api.post_task(body); task_id = created.get("posts_id")
    if not task_id: raise InstallError("A ADVBOX não devolveu o ID da tarefa de teste.")
    rows = api.get(f"/posts?id={task_id}&limit=2&offset=0").get("data", [])
    if len(rows) != 1 or str(rows[0].get("id")) != str(task_id): raise InstallError("A leitura de volta não confirmou o teste.")
    return {"task_id": task_id, "read_back": True, "must_be_completed_manually": True}

def result(data, status, config, ui, test):
    settings = data["settings"]
    return {"status": status, "package": MANIFEST["package_name"], "version": MANIFEST["version"],
            "verified_at": now(), "mode": MANIFEST["mode"], "queue_source": "advbox",
            "autos_source": "sync_read_only", "missing_task_types": data["missing_task_types"],
            "task_mapping": data["task_mapping"], "flowter": MANIFEST["flowter"],
            "catalogs": {"users": len(settings.get("users", [])), "tasks": len(settings.get("tasks", [])),
                         "stages": len(settings.get("stages", []))}, "ui_evidence": ui,
            "kit_local_config": str(config) if config else None, "test_task": test,
            "credential_stored": False, "human_review": True, "manual_filing": True}

def main() -> int:
    p = argparse.ArgumentParser(); p.add_argument("--kit-root", type=Path, default=Path.cwd())
    p.add_argument("--verify-only", action="store_true"); p.add_argument("--evidencia-interface", type=Path)
    p.add_argument("--test-lawsuit-id"); p.add_argument("--test-user-id"); p.add_argument("--output", type=Path)
    args = p.parse_args(); wants_test = bool(args.test_lawsuit_id or args.test_user_id)
    if wants_test and not (args.test_lawsuit_id and args.test_user_id): raise InstallError("O teste exige os dois IDs.")
    api = API(token_from_environment(), allow_task_creation=wants_test); data = audit(api); ui = evidence(args.evidencia_interface)
    status = "acao_na_interface" if data["missing_task_types"] or not ui else "aprovado"; config = None
    if status == "aprovado" and not args.verify_only: config = configure_kit(args.kit_root.resolve(), data, ui)
    test = test_task(api, data, args.test_lawsuit_id, args.test_user_id) if wants_test else None
    output = args.output or args.kit_root.resolve() / ".metodo-euro-runtime/integracoes/advbox/resultado_instalacao.json"
    atomic_json(output, result(data, status, config, ui, test))
    if status != "aprovado":
        print("AÇÃO GUIADA NECESSÁRIA — configure tarefas e Flowter conforme GUIA_CONFIGURACAO_ADVBOX.md")
        print("RESULTADO:", output); return 20
    print("INSTALAÇÃO APROVADA — ADVBOX é a fila operacional; protocolo continua manual.")
    print("RESULTADO:", output); return 0

if __name__ == "__main__":
    try: raise SystemExit(main())
    except InstallError as exc: raise SystemExit(f"INSTALAÇÃO NÃO CONCLUÍDA — {exc}")

#!/usr/bin/env python3
"""Instalador público e idempotente do Meu Estagiário no Kit 3."""
from __future__ import annotations

import argparse
import getpass
import json
import os
import shutil
import ssl
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MANIFEST = json.loads((ROOT / "manifesto.json").read_text(encoding="utf-8"))


class InstallError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class API:
    def __init__(self, token: str, base: str = MANIFEST["api_base"], timeout: int = 30):
        self.token = token.strip()
        self.base = base.rstrip("/")
        self.timeout = timeout

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> Any:
        if method not in {"GET", "POST", "PATCH", "PUT"}:
            raise InstallError(f"Método bloqueado pelo instalador: {method}")
        data = json.dumps(body, ensure_ascii=False).encode() if body is not None else None
        url = self.base + path
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": "Bear" + f"er {self.token}", "Accept": "application/json",
            "Content-Type": "application/json", "User-Agent": "Kit3-ME-Installer/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=self.timeout, context=ssl_context()) as res:
                raw = res.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:800]
            raise InstallError(f"Meu Estagiário respondeu HTTP {exc.code} em {method} {path}: {detail}") from exc
        except urllib.error.URLError as exc:
            if "CERTIFICATE_VERIFY_FAILED" in str(exc) and shutil.which("curl"):
                return self._curl(method, url, body)
            raise InstallError(f"Falha de rede no Meu Estagiário: {exc}") from exc

    def _curl(self, method: str, url: str, body: dict[str, Any] | None) -> Any:
        header = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
        payload = None
        try:
            os.chmod(header.name, 0o600)
            header.write("Authorization: Bear" + f"er {self.token}\nAccept: application/json\nContent-Type: application/json\n")
            header.close()
            cmd = ["curl", "-sS", "--fail-with-body", "-A", "Kit3-ME-Installer/1.0",
                   "-X", method, "-H", f"@{header.name}", "--max-time", str(self.timeout)]
            if body is not None:
                payload = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8")
                os.chmod(payload.name, 0o600)
                json.dump(body, payload, ensure_ascii=False); payload.close()
                cmd += ["--data-binary", f"@{payload.name}"]
            cmd.append(url)
            done = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 5)
            if done.returncode:
                raise InstallError(f"Meu Estagiário recusou {method}: {(done.stderr or done.stdout)[:800]}")
            return json.loads(done.stdout) if done.stdout.strip() else {}
        finally:
            Path(header.name).unlink(missing_ok=True)
            if payload:
                Path(payload.name).unlink(missing_ok=True)

    def get(self, path: str) -> Any: return self.request("GET", path)
    def post(self, path: str, body: dict[str, Any]) -> Any: return self.request("POST", path, body)
    def patch(self, path: str, body: dict[str, Any]) -> Any: return self.request("PATCH", path, body)


def token_from_environment() -> str:
    token = os.getenv(MANIFEST["credential_env"], "").strip()
    return token or getpass.getpass("Chave do Meu Estagiário (não será exibida): ").strip()


def scopes(identity: dict[str, Any]) -> set[str]:
    raw = identity.get("_scopes") or identity.get("escopos") or identity.get("scopes") or []
    return {str(item) for item in raw}


def require_scopes(identity: dict[str, Any], write: bool = False) -> None:
    available = scopes(identity)
    if not available:  # Chave sem escopos declarados recebe o acesso do usuário dono.
        return
    required = {"casos:leitura", "tarefas:leitura"}
    if write:
        required.add("tarefas:escrita")
    missing = sorted(required - available)
    if missing:
        raise InstallError("A chave não possui os escopos necessários: " + ", ".join(missing))


def audit(api: API, write: bool = False) -> dict[str, Any]:
    openapi = api.get("/openapi.json")
    api_version = str((openapi.get("info") or {}).get("version") or "")
    if not api_version or not isinstance(openapi.get("paths"), dict):
        raise InstallError("O contrato OpenAPI ao vivo não pôde ser validado.")
    identity_payload = api.get("/eu")
    identity = identity_payload.get("usuario") or identity_payload.get("eu") or identity_payload
    if not isinstance(identity, dict) or not identity:
        raise InstallError("A API não devolveu a identidade da chave.")
    identity = dict(identity)
    identity["workspace_id"] = identity_payload.get("workspace_id") or identity.get("workspace_id")
    identity["_scopes"] = (identity_payload.get("chave") or {}).get("escopos") or identity.get("escopos") or []
    require_scopes(identity, write)
    members = api.get("/membros").get("membros", [])
    types = api.get("/tarefas/tipos").get("tipos", [])
    stages = api.get("/casos/etapas").get("etapas", [])
    if not isinstance(members, list) or not isinstance(types, list) or not isinstance(stages, list):
        raise InstallError("Os catálogos da conta vieram em formato incompatível.")
    return {"identity": identity, "members": members, "task_types": types, "case_stages": stages,
            "api_version": api_version}


def configure_kit(kit_root: Path, audit_data: dict[str, Any]) -> Path:
    local_path = kit_root / ".escritorio.local.json"
    if not local_path.is_file():
        raise InstallError("A configuração local do Kit não existe; instale primeiro o núcleo do Kit 3.")
    local = json.loads(local_path.read_text(encoding="utf-8"))
    if local.get("repositorio_privado_confirmado") is not True:
        raise InstallError("O repositório privado operacional ainda não foi confirmado.")
    identity = audit_data["identity"]
    local.setdefault("integracoes", {})["meu_estagiario"] = {
        "habilitado": True,
        "modo": MANIFEST["mode"],
        "api_base": MANIFEST["api_base"],
        "credencial": {"variavel": MANIFEST["credential_env"]},
        "status_map": MANIFEST["status_map"],
        "workspace_id": identity.get("workspace_id") or (identity.get("workspace") or {}).get("id"),
        "configurado_em": now(),
    }
    atomic_json(local_path, local)
    return local_path


def synthetic_test(api: API) -> dict[str, Any]:
    marker = f"KIT3_TESTE:{uuid.uuid4()}"
    created = api.post("/tarefas", {
        "titulo": "[TESTE KIT3] Integração",
        "descricao": f"Registro sintético, sem dados reais. [{marker}]",
    }).get("tarefa", {})
    task_id = created.get("id")
    if not task_id:
        raise InstallError("A API não devolveu o ID da tarefa sintética.")
    states = []
    for status in ("in_progress", "in_review"):
        api.patch(f"/tarefas/{task_id}", {"status": status})
        current = api.get(f"/tarefas/{task_id}").get("tarefa", {})
        if current.get("status") != status:
            raise InstallError(f"A leitura de volta não confirmou o estado {status}.")
        states.append(status)
    api.post(f"/tarefas/{task_id}/notas", {"texto": "Teste técnico concluído; nenhum caso real foi utilizado."})
    api.patch(f"/tarefas/{task_id}", {"arquivada": True})
    return {"task_id": task_id, "states_verified": states, "archived": True}


def public_result(audit_data: dict[str, Any], config_path: Path | None, test: dict[str, Any] | None) -> dict[str, Any]:
    identity = audit_data["identity"]
    return {
        "status": "aprovado", "package": MANIFEST["package_name"], "version": MANIFEST["version"],
        "verified_at": now(), "api_contract": audit_data["api_version"],
        "workspace_id": identity.get("workspace_id") or (identity.get("workspace") or {}).get("id"),
        "catalogs": {"members": len(audit_data["members"]), "task_types": len(audit_data["task_types"]),
                     "case_stages": len(audit_data["case_stages"])},
        "kit_local_config": str(config_path) if config_path else None,
        "synthetic_test": test,
        "credential_stored": False, "manual_filing": True,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--kit-root", type=Path, default=Path.cwd())
    p.add_argument("--verify-only", action="store_true")
    p.add_argument("--test-write", action="store_true")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    api = API(token_from_environment())
    data = audit(api, write=args.test_write)
    config_path = None if args.verify_only else configure_kit(args.kit_root.resolve(), data)
    test = synthetic_test(api) if args.test_write else None
    result = public_result(data, config_path, test)
    output = args.output or args.kit_root.resolve() / ".esteira-runtime/integracoes/meu-estagiario/resultado_instalacao.json"
    atomic_json(output, result)
    print("INSTALAÇÃO APROVADA — Meu Estagiário conectado; protocolo continua manual.")
    print("RESULTADO:", output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InstallError as exc:
        raise SystemExit(f"INSTALAÇÃO NÃO CONCLUÍDA — {exc}")

#!/usr/bin/env python3
"""Espelha uma tarefa do Kit no Meu Estagiário com marcador idempotente."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Any

from instalar import API, InstallError, MANIFEST, audit, token_from_environment


def norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).casefold().split())


def paged(api: API, path: str, key: str) -> list[dict[str, Any]]:
    rows, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        payload = api.get(f"{path}{sep}pagina={page}&por_pagina=100")
        rows.extend(payload.get(key, []))
        if not payload.get("tem_mais"):
            return rows
        page += 1


def exact_member(members: list[dict[str, Any]], name: str) -> str | None:
    if not name:
        return None
    matches = [m for m in members if norm(m.get("nome") or m.get("name")) == norm(name)]
    return str(matches[0].get("id")) if len(matches) == 1 else None


def exact_case(api: API, cnj: str) -> str | None:
    query = urllib.parse.urlencode({"busca": cnj, "escopo": "escritorio"})
    matches = [c for c in paged(api, f"/casos?{query}", "casos") if norm(c.get("cnj")) == norm(cnj)]
    return str(matches[0].get("id")) if len(matches) == 1 else None


def marker(task_id: str) -> str:
    return f"[KIT3_TAREFA:{task_id}]"


def find_existing(api: API, task_id: str) -> dict[str, Any] | None:
    wanted = marker(task_id)
    matches = [t for t in paged(api, "/tarefas?incluir_arquivadas=true", "tarefas")
               if wanted in str(t.get("descricao") or "")]
    if len(matches) > 1:
        raise InstallError("Há mais de uma tarefa do Meu Estagiário com o mesmo ID do Kit.")
    return matches[0] if matches else None


def mirror(api: API, task: dict[str, Any], members: list[dict[str, Any]]) -> dict[str, Any]:
    task_id = str(task["id"])
    status = MANIFEST["status_map"].get(task.get("status"))
    if not status:
        raise InstallError("Status do Kit sem mapeamento para o Meu Estagiário.")
    description = "\n".join(filter(None, [
        marker(task_id),
        f"Referência: {task.get('referencia_entrada', '')}",
        f"Providência: {task.get('providencia_sugerida', '')}",
        "Autos: Sync em somente leitura. Revisão humana e protocolo manual.",
    ]))
    body: dict[str, Any] = {"titulo": f"Esteira — {task.get('referencia_entrada') or task_id}",
                            "descricao": description, "status": status}
    case_id = exact_case(api, str(task.get("cnj") or "")) if task.get("cnj") else None
    if case_id:
        body["caso_id"] = case_id
    responsible_id = exact_member(members, str(task.get("responsavel") or task.get("advogado") or ""))
    if responsible_id:
        body.update({"responsavel_tipo": "pessoa", "responsavel_id": responsible_id})
    current = find_existing(api, task_id)
    if current:
        task_id_me = str(current["id"])
        api.patch(f"/tarefas/{task_id_me}", body)
        action = "updated"
    else:
        body.pop("status")
        created = api.post("/tarefas", body).get("tarefa", {})
        task_id_me = str(created.get("id") or "")
        if not task_id_me:
            raise InstallError("A API não devolveu o ID da tarefa criada.")
        api.patch(f"/tarefas/{task_id_me}", {"status": status})
        action = "created"
    verified = api.get(f"/tarefas/{task_id_me}").get("tarefa", {})
    if verified.get("status") != status or marker(str(task["id"])) not in str(verified.get("descricao") or ""):
        raise InstallError("A leitura de volta não confirmou o espelhamento.")
    return {"action": action, "kit_task_id": task["id"], "me_task_id": task_id_me,
            "status": status, "case_linked": bool(case_id), "responsible_linked": bool(responsible_id)}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("task_json", type=Path)
    args = p.parse_args()
    task = json.loads(args.task_json.read_text(encoding="utf-8"))
    api = API(token_from_environment())
    data = audit(api, write=True)
    print(json.dumps(mirror(api, task, data["members"]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (InstallError, KeyError, json.JSONDecodeError) as exc:
        raise SystemExit(f"ESPELHAMENTO NÃO CONCLUÍDO — {exc}")

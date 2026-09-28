#!/usr/bin/env python3
"""Cria, de forma idempotente, a próxima tarefa da Esteira dentro da ADVBOX."""
from __future__ import annotations
import argparse, json, urllib.parse
from datetime import date
from instalar import API, InstallError, MANIFEST, audit, token_from_environment

def marker(external_id: str) -> str: return f"[KIT3_TAREFA:{external_id}]"

def existing(api: API, lawsuit_id: str, external_id: str) -> dict | None:
    wanted = marker(external_id); quoted = urllib.parse.quote(lawsuit_id); rows = []
    paths = [f"/posts?lawsuit_id={quoted}&limit=1000&offset=0",
             f"/posts?lawsuit_id={quoted}&completed_start=2000-01-01&completed_end={date.today().isoformat()}&limit=1000&offset=0"]
    for path in paths: rows.extend(api.get(path).get("data", []))
    found = {str(x.get("id")): x for x in rows if wanted in str(x.get("notes") or x.get("comments") or "")}
    if len(found) > 1: raise InstallError("Mais de uma tarefa possui o mesmo marcador da Esteira.")
    return next(iter(found.values())) if found else None

def create(api: API, stage: str, lawsuit_id: str, user_id: str, external_id: str,
           description: str, confirm: bool) -> dict:
    data = audit(api); task_type = data["task_mapping"].get(stage)
    if not task_type: raise InstallError(f"O tipo de tarefa da etapa {stage} ainda não existe.")
    found = existing(api, lawsuit_id, external_id)
    if found: return {"action": "already_exists", "post_id": found.get("id"), "external_id": external_id}
    payload = {"from": user_id, "guests": [user_id], "tasks_id": task_type, "lawsuits_id": lawsuit_id,
               "start_date": date.today().isoformat(), "comments": f"{marker(external_id)}\n{description}"}
    if not confirm: return {"action": "dry_run", "payload": payload}
    created = api.post_task(payload); post_id = created.get("posts_id")
    if not post_id: raise InstallError("A ADVBOX não devolveu o ID da tarefa criada.")
    rows = api.get(f"/posts?id={post_id}&limit=2&offset=0").get("data", [])
    if len(rows) != 1: raise InstallError("A leitura de volta não confirmou a nova tarefa.")
    return {"action": "created", "post_id": post_id, "external_id": external_id, "read_back": True}

def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--etapa", required=True, choices=[x["key"] for x in MANIFEST["task_types"]])
    p.add_argument("--lawsuit-id", required=True); p.add_argument("--user-id", required=True)
    p.add_argument("--external-id", required=True); p.add_argument("--descricao", required=True)
    p.add_argument("--confirmar", action="store_true"); args = p.parse_args()
    api = API(token_from_environment(), allow_task_creation=args.confirmar)
    print(json.dumps(create(api, args.etapa, args.lawsuit_id, args.user_id, args.external_id,
                            args.descricao, args.confirmar), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try: main()
    except InstallError as exc: raise SystemExit(f"TAREFA NÃO CRIADA — {exc}")

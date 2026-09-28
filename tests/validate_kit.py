#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
from pathlib import Path

root = Path(__file__).parents[1]
required = ["README.md", "AGENTS.md", "CLAUDE.md", "euro.py", "escritorio.json",
            "skills/configurar-kit3/SKILL.md",
            "skills/executar-tarefa/SKILL.md", "skills/revisar-entrega/SKILL.md",
            "skills/evoluir-skill/SKILL.md", "skills/resumo-do-processo/SKILL.md",
            "skills/gerar-peticao-por-modelo/SKILL.md", "skills/atualizar-kit/SKILL.md",
            "skills/conectar-software-juridico/SKILL.md",
            "versao-kit.json", "manifesto-arquivos.json",
            "integracoes/infinitum/Instalador-Esteira-Peticoes-Infinitum-v1.0.0.zip",
            "integracoes/infinitum/Instalador-Esteira-Peticoes-Infinitum-v1.0.0.zip.sha256",
            "integracoes/meu-estagiario/pacote/instalar.py",
            "integracoes/meu-estagiario/pacote/ponte.py",
            "integracoes/meu-estagiario/Instalador-Esteira-Peticoes-Meu-Estagiario-v1.0.0.zip",
            "integracoes/meu-estagiario/Instalador-Esteira-Peticoes-Meu-Estagiario-v1.0.0.zip.sha256",
            "integracoes/advbox/pacote/instalar.py",
            "integracoes/advbox/pacote/ponte.py",
            "integracoes/advbox/Instalador-Esteira-Peticoes-ADVBOX-v1.1.0-preview.zip",
            "integracoes/advbox/Instalador-Esteira-Peticoes-ADVBOX-v1.1.0-preview.zip.sha256"]
missing = [p for p in required if not (root / p).is_file()]
if missing:
    raise SystemExit("Arquivos ausentes: " + ", ".join(missing))
cfg = json.loads((root / "escritorio.json").read_text())
assert cfg["modo"] == "mvp"
assert cfg["conectores"]["sync"]["somente_leitura"] is True
assert cfg["conectores"]["sync"]["obrigatorio"] is True
assert cfg["fonte_autos"] == "sync"
assert cfg["conectores"]["infinitum"]["habilitado"] is False
assert cfg["conectores"]["meu_estagiario"]["habilitado"] is False
assert cfg["conectores"]["advbox"]["habilitado"] is False
assert cfg["conectores"]["advbox"]["modo"] == "advbox_operacional"
assert cfg["gates"]["protocolo_manual"] is True
signatures = ("gh" + "p_", "github" + "_pat_", "sk-" + "ant-", "Bear" + "er ")
for secret in signatures:
    for path in root.rglob("*"):
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts and path != Path(__file__) and secret in path.read_text(errors="ignore"):
            raise SystemExit(f"Possível segredo em {path}")
result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=root)
if result.returncode:
    raise SystemExit(result.returncode)
for suite in ("integracoes/meu-estagiario/pacote/tests", "integracoes/advbox/pacote/tests"):
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", suite, "-v"], cwd=root)
    if result.returncode:
        raise SystemExit(result.returncode)
result = subprocess.run([sys.executable, "tests/integration_single_office.py"], cwd=root)
if result.returncode:
    raise SystemExit(result.returncode)
for directory, archive in (
    ("integracoes/meu-estagiario", "Instalador-Esteira-Peticoes-Meu-Estagiario-v1.0.0.zip"),
    ("integracoes/advbox", "Instalador-Esteira-Peticoes-ADVBOX-v1.1.0-preview.zip"),
):
    expected = (root / directory / f"{archive}.sha256").read_text().split()[0]
    actual = hashlib.sha256((root / directory / archive).read_bytes()).hexdigest()
    if actual != expected:
        raise SystemExit(f"Checksum inválido: {archive}")
raise SystemExit(0)

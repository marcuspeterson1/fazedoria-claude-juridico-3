import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
import instalar  # noqa: E402
import ponte  # noqa: E402


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.tasks = []

    def get(self, path):
        self.calls.append(("GET", path, None))
        if path == "/openapi.json": return {"info": {"version": "1.9.0"}, "paths": {"/v1/eu": {"get": {}}}}
        if path == "/eu": return {"usuario": {"id": "u1"}, "workspace_id": "w1", "chave": {"escopos": ["casos:leitura", "tarefas:leitura", "tarefas:escrita"]}}
        if path == "/membros": return {"membros": [{"id": "m1", "nome": "Pessoa Teste"}]}
        if path == "/tarefas/tipos": return {"tipos": [{"id": "t1", "nome": "Manifestação"}]}
        if path == "/casos/etapas": return {"etapas": [{"id": "e1", "nome": "Ativo"}]}
        if path.startswith("/casos?"): return {"casos": [{"id": "c1", "cnj": "0000000-00.2026.0.00.0000"}], "tem_mais": False}
        if path.startswith("/tarefas?"): return {"tarefas": self.tasks, "tem_mais": False}
        if path.startswith("/tarefas/"):
            item = next(t for t in self.tasks if t["id"] == path.split("/")[2])
            return {"tarefa": dict(item)}
        raise AssertionError(path)

    def post(self, path, body):
        self.calls.append(("POST", path, body))
        if path == "/tarefas":
            item = {"id": f"me-{len(self.tasks)+1}", "status": "todo", **body}
            self.tasks.append(item); return {"tarefa": dict(item)}
        if path.endswith("/notas"): return {"nota": {"id": "n1", **body}}
        raise AssertionError(path)

    def patch(self, path, body):
        self.calls.append(("PATCH", path, body))
        item = next(t for t in self.tasks if t["id"] == path.split("/")[2])
        item.update(body); return {"tarefa": dict(item)}


class InstallerTests(unittest.TestCase):
    def test_audit_is_read_only(self):
        api = FakeAPI(); data = instalar.audit(api)
        self.assertEqual(1, len(data["members"]))
        self.assertEqual("1.9.0", data["api_version"])
        self.assertTrue(all(method == "GET" for method, _, _ in api.calls))

    def test_configuration_stores_variable_not_token(self):
        api = FakeAPI(); data = instalar.audit(api)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".escritorio.local.json").write_text(json.dumps({"repositorio_privado_confirmado": True}))
            path = instalar.configure_kit(root, data)
            text = path.read_text()
            self.assertIn("MEU_ESTAGIARIO_API_KEY", text)
            self.assertNotIn("mea_segredo", text)

    def test_synthetic_test_reads_states_back_and_archives(self):
        api = FakeAPI(); result = instalar.synthetic_test(api)
        self.assertEqual(["in_progress", "in_review"], result["states_verified"])
        self.assertTrue(api.tasks[0]["arquivada"])
        self.assertFalse(any(method == "DELETE" for method, _, _ in api.calls))

    def test_bridge_is_idempotent(self):
        api = FakeAPI(); members = instalar.audit(api, write=True)["members"]
        task = {"id": "kit-1", "status": "aberta", "cnj": "0000000-00.2026.0.00.0000",
                "referencia_entrada": "Manifestação", "providencia_sugerida": "Preparar minuta",
                "responsavel": "Pessoa Teste"}
        first = ponte.mirror(api, task, members)
        second = ponte.mirror(api, {**task, "status": "em_execucao"}, members)
        self.assertEqual("created", first["action"])
        self.assertEqual("updated", second["action"])
        self.assertEqual(1, len(api.tasks))
        self.assertEqual("in_progress", api.tasks[0]["status"])


if __name__ == "__main__": unittest.main()

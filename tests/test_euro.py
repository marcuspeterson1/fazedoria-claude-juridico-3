import importlib.util
import json
import tempfile
import unittest
import contextlib
import io
import os
from pathlib import Path
from unittest import mock

SPEC = importlib.util.spec_from_file_location("euro", Path(__file__).parents[1] / "euro.py")
euro = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(euro)
SYNC_SPEC = importlib.util.spec_from_file_location("kit_sync", Path(__file__).parents[1] / "conectores" / "sync.py")
kit_sync = importlib.util.module_from_spec(SYNC_SPEC)
SYNC_SPEC.loader.exec_module(kit_sync)

class EuroTests(unittest.TestCase):
    def test_state_machine_rejects_skip(self):
        data = {"status": "aberta"}
        with self.assertRaises(SystemExit):
            euro.transition(data, "aprovada")

    def test_state_machine_happy_path(self):
        data = {"status": "aberta"}
        for state in ("em_execucao", "entregue", "aprovada"):
            euro.transition(data, state)
        self.assertEqual(data["status"], "aprovada")

    def test_start_office_grants_every_role_alone(self):
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(euro, "ROOT", Path(d)), \
             mock.patch.object(euro, "LOCAL", Path(d) / ".escritorio.local.json"), \
             mock.patch.object(euro, "SHARED", Path(d) / "escritorio.json"):
            euro.save(euro.SHARED, {"nome_escritorio": "CONFIGURE-ME", "organizacao": None, "modo": "mvp"})
            parsed = euro.parser().parse_args(["iniciar-escritorio", "--nome", "Marcus", "--escritorio", "E",
                                                "--repositorio", "https://example.invalid/r"])
            parsed.fn(parsed)
            local = euro.load(euro.LOCAL)
            self.assertEqual(set(local["papeis"]), {"dono", "controller", "advogado"})

    def test_document_policy_is_owner_command(self):
        parsed = euro.parser().parse_args(["configurar-documentos", "--onde-modelos", "Drive", "--pastas-clientes", "sim", "--destino-copia", "Pasta do cliente", "--padrao-nomes", "TIPO - CLIENTE"])
        self.assertEqual(parsed.onde_modelos, "Drive")

    def test_delivery_requires_model_traceability(self):
        with self.assertRaises(SystemExit):
            euro.parser().parse_args(["entregar", "tarefa", "minuta.docx"])

    def test_daily_card_shows_the_single_flow(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            euro.print_daily_card({"papeis": ["dono", "controller", "advogado"]})
        self.assertIn("/executar-tarefa", out.getvalue())

    def test_sync_materializes_chronology_and_markdown_locally(self):
        class FakeSync:
            def autos(self, _cnj):
                return {"total": 2, "capa": {}, "autos": [
                    {"tipo": "movimento", "data": "2026-01-01", "descricao": "Despacho"},
                    {"tipo": "documento", "data": "2026-01-02", "id": 7,
                     "nome": "decisão.pdf", "tipo_documento": "Decisão", "tem_markdown": True},
                ]}
            def markdown(self, documento_id):
                return f"# Documento {documento_id}\n"
        with tempfile.TemporaryDirectory() as d:
            entrada = kit_sync.materializar_entrada("000", Path(d) / "entrada", "org", FakeSync())
            self.assertTrue((entrada / "0000-CRONOLOGIA.md").is_file())
            self.assertEqual(len(list(entrada.glob("*7*.md"))), 1)
            manifesto = json.loads((entrada / "manifesto-sync.json").read_text())
            self.assertEqual(manifesto["total"], 2)
            self.assertTrue(manifesto["leitura_integral_confirmada"])

    def test_sync_manifest_blocks_integral_confirmation_when_document_is_unavailable(self):
        class FakeSync:
            def autos(self, _cnj):
                return {"total": 1, "capa": {}, "autos": [
                    {"tipo": "documento", "data": "2026-01-02", "id": 8,
                     "nome": "anexo.pdf", "tipo_documento": "Anexo", "tem_markdown": False},
                ]}
        with tempfile.TemporaryDirectory() as d:
            entrada = kit_sync.materializar_entrada("000", Path(d) / "entrada", "org", FakeSync())
            manifesto = json.loads((entrada / "manifesto-sync.json").read_text())
            self.assertFalse(manifesto["leitura_integral_confirmada"])
            self.assertEqual(len(manifesto["indisponiveis"]), 1)

    def test_sync_intimations_are_paginated_only_with_gets(self):
        respostas = [
            {"total": 201, "intimacoes": [{"id": i} for i in range(200)]},
            {"total": 201, "intimacoes": [{"id": 200}]},
        ]
        cliente = kit_sync.ClienteSync("segredo")
        with mock.patch.object(cliente, "_get", side_effect=respostas) as get:
            itens = cliente.intimacoes()
        self.assertEqual(len(itens), 201)
        self.assertEqual(get.call_count, 2)
        self.assertTrue(all(call.args[0] == "/v1/intimacoes" for call in get.call_args_list))

    def test_daily_inbox_deduplicates_and_does_not_create_tasks(self):
        class FakeSync:
            def intimacoes(self, status, dias):
                return [{"id": 42, "processo": "000", "data": "2026-09-08",
                         "tipo_ato": "despacho", "data_fatal": "2026-09-15"}]
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(euro, "INBOX_DIR", Path(d)), \
             mock.patch.object(euro, "INBOX_STATE", Path(d) / "intimacoes.json"):
            local = {"organizacao_id": "org"}
            _inbox, novas, consultou = euro.atualizar_inbox_intimacoes(local, FakeSync(), True, "2026-09-08")
            self.assertEqual(novas, 1)
            self.assertTrue(consultou)
            _inbox, novas, consultou = euro.atualizar_inbox_intimacoes(local, FakeSync(), True, "2026-09-08")
            self.assertEqual(novas, 0)
            self.assertFalse(consultou)
            self.assertFalse(any(Path(d).glob("fila/*.json")))

    def test_parser_requires_controller_confirmation_to_import_intimation(self):
        with self.assertRaises(SystemExit):
            euro.parser().parse_args(["importar-intimacao", "42"])
        parsed = euro.parser().parse_args(["importar-intimacao", "42", "--providencia", "Analisar"])
        self.assertEqual(parsed.id_sync, 42)

    def test_auto_sync_prepares_daily_inbox_and_windows_logon_trigger(self):
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(euro, "ROOT", Path(d)), \
             mock.patch.object(euro.platform, "system", return_value="Windows"):
            euro.cmd_prepare_auto_sync(None)
            runner = (Path(d) / ".esteira-runtime" / "auto-sync.py").read_text()
            task = (Path(d) / ".esteira-runtime" / "INSTALAR-TAREFA-WINDOWS.ps1").read_text()
            self.assertIn("checar-intimacoes", runner)
            self.assertIn("--somente-se-dia-novo", runner)
            self.assertIn("New-ScheduledTaskTrigger -AtLogOn", task)

    def test_existing_secure_env_file_can_be_reused(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / ".secrets.env"
            path.write_text("ATENDE_DIREITO_SYNC_KEY='valor-local'\n", encoding="utf-8")
            self.assertEqual(kit_sync._ler_env(path)["ATENDE_DIREITO_SYNC_KEY"], "valor-local")

    def test_general_claude_config_is_never_scanned_for_sync_key(self):
        with tempfile.TemporaryDirectory() as d:
            home = Path(d)
            (home / ".claude").mkdir()
            (home / ".claude" / "settings.json").write_text(
                '{"url":"https://sync.atendedireito.app","token":"sk_outra_integracao"}',
                encoding="utf-8")
            with mock.patch.object(kit_sync.Path, "home", return_value=home), mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(kit_sync.descobrir_chave_existente("org"), (None, None))

    def test_windows_subprocesses_are_hidden(self):
        with mock.patch.object(euro.platform, "system", return_value="Windows"):
            self.assertIn("creationflags", euro.hidden_subprocess_kwargs())

    def test_skill_link_preserves_existing(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "source"; source.mkdir()
            target = Path(d) / "target"; target.mkdir()
            self.assertIn("preservada", euro.link_skill(source, target))

    def test_skill_link_is_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "source"; source.mkdir()
            target = Path(d) / "target"
            self.assertEqual(euro.link_skill(source, target), "ligada")
            self.assertEqual(euro.link_skill(source, target), "já ligada")

if __name__ == "__main__":
    unittest.main()

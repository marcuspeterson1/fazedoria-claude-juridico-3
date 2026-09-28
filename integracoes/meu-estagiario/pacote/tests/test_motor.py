import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).parents[1]
KIT_ROOT_REAL = ROOT.parents[2]
sys.path.insert(0, str(ROOT))
import instalar  # noqa: E402
import ponte  # noqa: E402
import motor  # noqa: E402


class FakeAPI:
    """Mesma forma da FakeAPI de test_instalador.py, estendida com notas e listagem de tarefas."""

    def __init__(self):
        self.calls = []
        self.tasks: list[dict] = []
        self._next_note_id = 1

    def get(self, path):
        self.calls.append(("GET", path, None))
        if path == "/membros" or path.startswith("/membros?"):
            return {"membros": self.members}
        if path.startswith("/tarefas?"):
            return {"tarefas": self.tasks, "tem_mais": False}
        if path.startswith("/casos?"):
            return {"casos": getattr(self, "casos", []), "tem_mais": False}
        if path.startswith("/tarefas/"):
            item_id = path.split("/")[2]
            item = next(t for t in self.tasks if t["id"] == item_id)
            return {"tarefa": dict(item)}
        raise AssertionError(path)

    def post(self, path, body):
        self.calls.append(("POST", path, body))
        if path.endswith("/notas"):
            item_id = path.split("/")[2]
            item = next(t for t in self.tasks if t["id"] == item_id)
            nota = {"id": f"n{self._next_note_id}", "texto": body["texto"], "criada_em": f"2026-01-01T00:{self._next_note_id:02d}:00Z"}
            self._next_note_id += 1
            item.setdefault("notas", []).append(nota)
            return {"nota": nota}
        raise AssertionError(path)

    def patch(self, path, body):
        self.calls.append(("PATCH", path, body))
        item = next(t for t in self.tasks if t["id"] == path.split("/")[2])
        item.update(body)
        return {"tarefa": dict(item)}


def montar_kit_root(tmp: Path, papel: str, colaborador: str) -> Path:
    kit_root = tmp / "kit"
    kit_root.mkdir()
    shutil.copy(KIT_ROOT_REAL / "euro.py", kit_root / "euro.py")
    shutil.copytree(KIT_ROOT_REAL / "conectores", kit_root / "conectores")
    (kit_root / "fila").mkdir()
    (kit_root / ".metodo-euro.local.json").write_text(json.dumps({
        "colaborador": colaborador, "papeis": [papel], "papel": papel,
        "organizacao_id": "org-1", "repositorio_privado_confirmado": True,
        "integracoes": {"meu_estagiario": {"habilitado": True}},
    }), encoding="utf-8")
    (kit_root / "metodo-euro.json").write_text(json.dumps({
        "modo": "mvp", "nome_escritorio": "Escritório Teste",
        "organizacao": {"id": "org-1"},
        "producao_documental": {"modelo_obrigatorio": True},
    }), encoding="utf-8")
    return kit_root


def criar_tarefa_kit(kit_root: Path, kit_id: str, **extra) -> dict:
    dados = {"schema_version": 1, "id": kit_id, "status": "aberta", "modo": "mvp",
             "cnj": "0000000-00.2026.0.00.0000", "referencia_entrada": "ref", "fonte": "sync",
             "providencia_sugerida": "", "responsavel": None, "criada_por": "Dono Exemplo",
             "criada_em": "2026-01-01T00:00:00Z", "entrega": None, "revisao": None, "historico": []}
    dados.update(extra)
    (kit_root / "fila" / f"{kit_id}.json").write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    return dados


def ler_tarefa_kit(kit_root: Path, kit_id: str) -> dict:
    return json.loads((kit_root / "fila" / f"{kit_id}.json").read_text(encoding="utf-8"))


class ParseNotaTests(unittest.TestCase):
    def test_extrai_responsavel_e_providencia_rotulados(self):
        info = motor.parse_nota("Responsável: Leonardo Moraes\nProvidência: gerar manifestação de ciência")
        self.assertEqual(info["responsavel"], "Leonardo Moraes")
        self.assertEqual(info["providencia"], "gerar manifestação de ciência")
        self.assertTrue(info["automatizar"])

    def test_sem_linha_responsavel_fica_vazio(self):
        info = motor.parse_nota("Só um comentário qualquer, sem estrutura.")
        self.assertEqual(info["responsavel"], "")

    def test_nao_automatizar_desliga_flag(self):
        info = motor.parse_nota("Responsável: Leonardo Moraes\nNão automatizar, eu mesmo cuido.")
        self.assertEqual(info["responsavel"], "Leonardo Moraes")
        self.assertFalse(info["automatizar"])

    def test_texto_solto_vira_providencia_quando_sem_rotulo(self):
        info = motor.parse_nota("Responsável: Leonardo Moraes\nGerar manifestação de ciência, é urgente.")
        self.assertIn("Gerar manifestação", info["providencia"])

    def test_id_da_tarefa_kit(self):
        self.assertEqual(motor.id_da_tarefa_kit("[METODO_EURO_ID:20260101-abc] resto"), "20260101-abc")
        self.assertIsNone(motor.id_da_tarefa_kit("sem marcador nenhum"))


class CicloControllerTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.kit_root = montar_kit_root(self.tmp, "controller", "Dono Exemplo")
        self.local = json.loads((self.kit_root / ".metodo-euro.local.json").read_text())
        self.kit_id = "20260101-caso"
        criar_tarefa_kit(self.kit_root, self.kit_id)
        self.api = FakeAPI()
        self.api.members = [{"id": "m1", "nome": "Leonardo Moraes"}]
        self.api.tasks = [{"id": "me1", "status": "todo",
                            "descricao": f"[METODO_EURO_ID:{self.kit_id}] Referência: ref",
                            "notas": []}]

    def tearDown(self):
        self._tmp.cleanup()

    def test_atribui_quando_nota_tem_responsavel_exato(self):
        self.api.tasks[0]["notas"].append({
            "id": "n0", "criada_em": "2025-12-31T00:00:00Z",
            "texto": "Responsável: Leonardo Moraes\nProvidência: gerar manifestação de ciência",
        })
        relatorio = motor.ciclo_controller(self.api, self.kit_root, self.local, self.api.members)
        tarefa = ler_tarefa_kit(self.kit_root, self.kit_id)
        self.assertEqual(tarefa["responsavel"], "Leonardo Moraes")
        self.assertEqual(tarefa["providencia_sugerida"], "gerar manifestação de ciência")
        self.assertTrue(tarefa["automatizar"])
        self.assertTrue(any("atribuída" in linha for linha in relatorio))
        notas_robo = [n for n in self.api.tasks[0]["notas"] if n["texto"].startswith(motor.MARCADOR_ROBO)]
        self.assertEqual(len(notas_robo), 1)

    def test_pede_esclarecimento_quando_nome_nao_bate_exato(self):
        self.api.tasks[0]["notas"].append({
            "id": "n0", "criada_em": "2025-12-31T00:00:00Z",
            "texto": "Responsável: Pessoa Que Não Existe\nProvidência: gerar manifestação",
        })
        motor.ciclo_controller(self.api, self.kit_root, self.local, self.api.members)
        tarefa = ler_tarefa_kit(self.kit_root, self.kit_id)
        self.assertIsNone(tarefa["responsavel"])
        notas_robo = [n for n in self.api.tasks[0]["notas"] if n["texto"].startswith(motor.MARCADOR_ROBO)]
        self.assertEqual(len(notas_robo), 1)
        self.assertIn("Não achei exatamente", notas_robo[0]["texto"])

    def test_nao_reprocessa_a_mesma_nota_no_ciclo_seguinte(self):
        self.api.tasks[0]["notas"].append({
            "id": "n0", "criada_em": "2025-12-31T00:00:00Z",
            "texto": "Responsável: Leonardo Moraes\nProvidência: gerar manifestação",
        })
        motor.ciclo_controller(self.api, self.kit_root, self.local, self.api.members)
        chamadas_antes = len(self.api.calls)
        segundo = motor.ciclo_controller(self.api, self.kit_root, self.local, self.api.members)
        self.assertEqual(segundo, [])
        # segundo ciclo ainda lê (paged/get), mas não gera novo POST de atribuição/nota
        posts_apos = [c for c in self.api.calls[chamadas_antes:] if c[0] == "POST"]
        self.assertEqual(posts_apos, [])

    def test_ignora_notas_que_o_proprio_robo_escreveu(self):
        self.api.tasks[0]["notas"].append({
            "id": "n0", "criada_em": "2025-12-31T00:00:00Z",
            "texto": f"{motor.MARCADOR_ROBO} Atribuída a Leonardo Moraes.",
        })
        motor.ciclo_controller(self.api, self.kit_root, self.local, self.api.members)
        tarefa = ler_tarefa_kit(self.kit_root, self.kit_id)
        self.assertIsNone(tarefa["responsavel"])


class CicloAdvogadoTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.kit_root = montar_kit_root(self.tmp, "advogado", "Leonardo Moraes")
        self.local = json.loads((self.kit_root / ".metodo-euro.local.json").read_text())
        self.kit_id = "20260101-caso"
        criar_tarefa_kit(self.kit_root, self.kit_id, responsavel="Leonardo Moraes", automatizar=True)
        self.api = FakeAPI()
        self.api.members = [{"id": "m1", "nome": "Leonardo Moraes"}]
        self.api.tasks = [{"id": "me1", "status": "todo",
                            "descricao": f"[METODO_EURO_ID:{self.kit_id}] Referência: ref",
                            "notas": []}]
        real_executar = motor.executar_euro

        def contexto_simulado(kit_root, *args):
            if args and args[0] == "contexto":
                return subprocess.CompletedProcess(args, 0, stdout="ENTRADA AUTORIZADA: (simulada)\n", stderr="")
            return real_executar(kit_root, *args)

        patcher = mock.patch.object(motor, "executar_euro", side_effect=contexto_simulado)
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self._tmp.cleanup()

    def test_entrega_de_verdade_dispara_mirror_e_nota_de_sucesso(self):
        draft = self.tmp / "minuta.md"
        draft.write_text("<!-- RASCUNHO: NÃO PROTOCOLAR -->\nMinuta de teste.\n", encoding="utf-8")

        def executor_falso(kit_root, prompt):
            self.assertIn(self.kit_id, prompt)
            motor.executar_euro(kit_root, "entregar", self.kit_id, str(draft),
                                 "--modelo", "modelo-aprovado.docx", "--copia-destino", "Drive/Cliente/peça.docx")
            return subprocess.CompletedProcess([], 0, stdout="ok", stderr="")

        relatorio = motor.ciclo_advogado(self.api, self.kit_root, self.local, executor=executor_falso)
        tarefa = ler_tarefa_kit(self.kit_root, self.kit_id)
        self.assertEqual(tarefa["status"], "entregue")
        self.assertTrue(any("entregue e avisado" in linha for linha in relatorio))
        me_task = self.api.tasks[0]
        self.assertEqual(me_task["status"], "in_review")
        notas_robo = [n for n in me_task["notas"] if n["texto"].startswith(motor.MARCADOR_ROBO)]
        self.assertTrue(any("Minuta gerada e entregue" in n["texto"] for n in notas_robo))
        self.assertTrue(any("Drive/Cliente/peça.docx" in n["texto"] for n in notas_robo))

    def test_quando_nao_conclui_sozinho_avisa_para_continuacao_humana(self):
        def executor_que_nao_termina(kit_root, prompt):
            return subprocess.CompletedProcess([], 0, stdout="parei, faltou o modelo aprovado", stderr="")

        relatorio = motor.ciclo_advogado(self.api, self.kit_root, self.local, executor=executor_que_nao_termina)
        tarefa = ler_tarefa_kit(self.kit_root, self.kit_id)
        self.assertEqual(tarefa["status"], "em_execucao")
        self.assertTrue(any("não concluiu sozinho" in linha for linha in relatorio))
        notas_robo = [n for n in self.api.tasks[0]["notas"] if n["texto"].startswith(motor.MARCADOR_ROBO)]
        self.assertTrue(any("Não concluí a minuta sozinho" in n["texto"] for n in notas_robo))

    def test_ignora_tarefa_sem_flag_automatizar(self):
        criar_tarefa_kit(self.kit_root, "20260102-manual", responsavel="Leonardo Moraes", automatizar=False)
        chamado = {"n": 0}

        def executor_que_conta(kit_root, prompt):
            chamado["n"] += 1
            return subprocess.CompletedProcess([], 0, stdout="", stderr="")

        motor.ciclo_advogado(self.api, self.kit_root, self.local, executor=executor_que_conta)
        # só a tarefa com automatizar=True (kit_id) deveria disparar o headless
        self.assertEqual(chamado["n"], 1)
        manual = ler_tarefa_kit(self.kit_root, "20260102-manual")
        self.assertEqual(manual["status"], "aberta")


if __name__ == "__main__":
    unittest.main()

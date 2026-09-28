import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).parents[1]; sys.path.insert(0, str(ROOT))
import instalar, ponte  # noqa: E402

def task_catalog():
    return [{"id": i, "task": spec["name"]} for i, spec in enumerate(instalar.MANIFEST["task_types"], 1)]

class FakeAPI:
    def __init__(self, complete=True): self.calls=[]; self.tasks=task_catalog() if complete else []; self.posts=[]
    def get(self,path):
        self.calls.append(("GET",path,None))
        if path=="/settings": return {"users":[{"id":9}],"tasks":self.tasks,"stages":[{}]}
        if path.startswith("/posts?id="):
            wanted=path.split("id=")[1].split("&")[0]; return {"data":[p for p in self.posts if str(p["id"])==wanted]}
        if path.startswith("/posts?"): return {"data":self.posts}
        raise AssertionError(path)
    def post_task(self,body):
        self.calls.append(("POST","/posts",body)); item={"id":len(self.posts)+1,"notes":body.get("comments"),**body}
        self.posts.append(item); return {"success":True,"posts_id":item["id"]}

class Tests(unittest.TestCase):
    def test_missing_catalog_requires_ui(self):
        data=instalar.audit(FakeAPI(False)); self.assertEqual(8,len(data["missing_task_types"]))
    def test_complete_catalog_maps_all_stages(self):
        data=instalar.audit(FakeAPI()); self.assertEqual(8,len(data["task_mapping"]))
    def test_api_blocks_every_write_except_controlled_post(self):
        api=instalar.API("x",base="https://example.invalid")
        for method in ("POST","PUT","PATCH","DELETE"):
            with self.assertRaises(instalar.InstallError): api.request(method,"/lawsuits")
    def test_test_task_is_read_back(self):
        api=FakeAPI(); result=instalar.test_task(api,instalar.audit(api),"77","9")
        self.assertTrue(result["read_back"]); self.assertEqual(1,len(api.posts))
    def test_bridge_dry_run_then_idempotent_creation(self):
        api=FakeAPI(); preview=ponte.create(api,"revisar","77","9","job-1","Link da minuta",False)
        self.assertEqual("dry_run",preview["action"]); self.assertEqual(0,len(api.posts))
        created=ponte.create(api,"revisar","77","9","job-1","Link da minuta",True)
        again=ponte.create(api,"revisar","77","9","job-1","Link da minuta",True)
        self.assertEqual("created",created["action"]); self.assertEqual("already_exists",again["action"])
        self.assertEqual(1,len(api.posts))

if __name__=="__main__": unittest.main()

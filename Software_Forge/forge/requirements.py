from __future__ import annotations
import hashlib, json
from pathlib import Path
from .manifest import ManifestEngine

class RequirementEngine:
    def __init__(self,root:Path):
        self.root=root.resolve()
        self.manifest=ManifestEngine(self.root)

    def build_graph(self):
        snap=self.manifest.snapshot()
        requirements=[]
        for r in snap["requirements"]["requirements"]:
            rid=r["id"]
            requirements.append({
                "requirement_id":rid,
                "manifest_path":r["path"],
                "status":"OBSERVED",
                "tests":[{"test_id":f"TEST-{hashlib.sha1((rid+':traceability').encode()).hexdigest()[:10].upper()}","type":"traceability","status":"OBSERVED"}],
                "evidence":[],
                "verification":"UNVERIFIED",
                "release_gate":False,
            })
        return {"manifest_sha256":snap["manifest"]["sha256"],"requirements":requirements}

    def persist(self):
        graph=self.build_graph()
        out=self.root/".forge/requirements.json"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(graph,indent=2),encoding="utf-8")
        return graph

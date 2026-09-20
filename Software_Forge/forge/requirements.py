from __future__ import annotations
import json
from pathlib import Path
from .manifest import ManifestEngine

class RequirementEngine:
    def __init__(self,root:Path): self.root=root.resolve(); self.manifest=ManifestEngine(self.root)
    def build_graph(self):
        snap=self.manifest.snapshot()
        return {"manifest_sha256":snap["manifest"]["sha256"],"requirements":[{"requirement_id":r["id"],"manifest_path":r["path"],"status":"OBSERVED","tests":[],"evidence":[],"verification":"UNVERIFIED","release_gate":False} for r in snap["requirements"]["requirements"]]}
    def persist(self):
        graph=self.build_graph(); out=self.root/".forge/requirements.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(graph,indent=2),encoding="utf-8"); return graph

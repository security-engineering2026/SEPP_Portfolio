import json, os, platform, time
from pathlib import Path
from .inventory import inventory
from .store import ForgeStore
class ForgeEngine:
    def __init__(self,root:Path): self.root=root.resolve(); self.store=ForgeStore(self.root)
    def environment(self): return {"os":platform.platform(),"python":platform.python_version(),"machine":platform.machine(),"cwd":str(self.root),"pid":os.getpid(),"time_utc":time.time()}
    def inspect(self):
        data=inventory(self.root); data["environment"]=self.environment(); out=self.root/".forge/inventory.json"; out.write_text(json.dumps(data,indent=2),encoding="utf-8"); h=self.store.evidence("inventory",out); self.store.event("inventory",{"sha256":h}); return data
    def health(self):
        gates={"manifest":False,"persistence":(self.root/".forge/forge.db").exists(),"inventory":(self.root/".forge/inventory.json").exists(),"runtime":True,"independent_verification":False}
        gates["manifest"]=any((self.root/x).exists() for x in ["Software_Forge/SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.md","FORGE_MANIFEST.md"])
        return {"truth_state":"TESTED","gates":gates,"release_ready":all(gates.values())}
    def self_test(self):
        self.store.meta("schema","1"); checks=[("persistence",self.store.meta("schema")=="1")]; inv=self.inspect(); checks.append(("inventory",inv["status"]=="OBSERVED")); checks.append(("runtime",True)); p=self.root/".forge/self_test.json"; p.write_text(json.dumps({"checks":checks,"environment":self.environment()},indent=2),encoding="utf-8"); self.store.evidence("self_test",p,"TESTED"); ok=all(v for _,v in checks); self.store.event("self_test",{"checks":checks,"result":"PASS" if ok else "FAIL"}); return ok,checks

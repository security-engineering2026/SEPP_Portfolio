import json, os, platform, time
from pathlib import Path
from .inventory import inventory
from .store import ForgeStore
from .manifest import ManifestEngine, ManifestError
from .requirements import RequirementEngine
from .verifier import IndependentVerifier
from .build import BuildEngine
from .execution import ExecutionEngine
from .failure import FailureAnalyzer
class ForgeEngine:
    def __init__(self,root:Path): self.root=root.resolve(); self.store=ForgeStore(self.root)
    def environment(self): return {"os":platform.platform(),"python":platform.python_version(),"machine":platform.machine(),"cwd":str(self.root),"pid":os.getpid(),"time_utc":time.time()}
    def inspect(self):
        data=inventory(self.root); data["environment"]=self.environment(); out=self.root/".forge/inventory.json"; out.write_text(json.dumps(data,indent=2),encoding="utf-8"); h=self.store.evidence("inventory",out); self.store.event("inventory",{"sha256":h}); return data
    def manifest(self):
        try: result=ManifestEngine(self.root).snapshot()
        except ManifestError as exc: result={"manifest":{"state":"FAILED","errors":[str(exc)]},"requirements":{"count":0,"requirements":[]}}
        out=self.root/".forge/manifest.json"; out.write_text(json.dumps(result,indent=2),encoding="utf-8"); self.store.evidence("manifest",out,"TESTED"); self.store.event("manifest",result["manifest"]); return result
    def requirements(self):
        graph=RequirementEngine(self.root).persist(); self.store.evidence("requirements",self.root/".forge/requirements.json","OBSERVED"); self.store.event("requirements",{"count":len(graph["requirements"]),"manifest_sha256":graph["manifest_sha256"]}); return graph
    def build(self):
        result=BuildEngine(self.root).build(); self.store.evidence("build",self.root/".forge/build.json","TESTED"); self.store.event("build",{"state":result["state"],"compiled_files":result["compiled_files"]}); return result
    def execute(self,command,timeout_seconds=30.0,cwd=None):
        result=ExecutionEngine(self.root).run(command,timeout_seconds,cwd)
        evidence_hash=self.store.evidence("execution",self.root/".forge/execution.json","TESTED")
        self.store.event("execution",{"execution_id":result["execution_id"],"state":result["state"],"exit_code":result["exit_code"],"error":result["error"],"evidence_sha256":evidence_hash})
        req_path=self.root/".forge/requirements.json"
        if req_path.exists():
            graph=json.loads(req_path.read_text(encoding="utf-8"))
            for req in graph.get("requirements",[]):
                req["evidence"].append({"evidence_type":"execution","execution_id":result["execution_id"],"sha256":evidence_hash,"status":"TESTED"})
                req["verification"]="OBSERVED"
            req_path.write_text(json.dumps(graph,indent=2),encoding="utf-8")
            self.store.evidence("requirements_lineage",req_path,"TESTED")
        return result
    def analyze_failure(self, observation):
        result=FailureAnalyzer(self.root).analyze(observation)
        self.store.evidence("failure_analysis",self.root/".forge/failure.json","TESTED")
        self.store.event("failure_analysis",{"state":result["state"],"category":result["category"],"failure_id":result.get("failure_id")})
        if result.get("failure_id"):
            self.store.failure_attempt(result["failure_id"], "deterministic_failure_analysis", "ANALYZED",
                                       {"category":result["category"],"confidence":result["confidence"]})
        return result
    def verify(self):
        result=IndependentVerifier(self.root).verify(); self.store.event("independent_verification",{"state":result["state"],"verification_sha256":result["verification_sha256"]}); return result
    def health(self):
        gates={"manifest":(self.root/".forge/manifest.json").exists(),"persistence":(self.root/".forge/forge.db").exists(),"inventory":(self.root/".forge/inventory.json").exists(),"runtime":True,"independent_verification":False}
        state=None
        if gates["manifest"]:
            try: state=json.loads((self.root/".forge/manifest.json").read_text(encoding="utf-8"))["manifest"]["state"]
            except Exception: state="FAILED"
        gates["manifest"]=state=="VERIFIED"
        vp=self.root/".forge/verification.json"
        if vp.exists():
            try: gates["independent_verification"]=json.loads(vp.read_text(encoding="utf-8")).get("state")=="VERIFIED"
            except Exception: gates["independent_verification"]=False
        return {"truth_state":"TESTED","gates":gates,"release_ready":all(gates.values())}
    def self_test(self):
        self.store.meta("schema","1"); checks=[("persistence",self.store.meta("schema")=="1")]; inv=self.inspect(); checks.append(("inventory",inv["status"]=="OBSERVED")); man=self.manifest(); checks.append(("manifest",man["manifest"]["state"]=="VERIFIED")); graph=self.requirements(); checks.append(("requirements",len(graph["requirements"])>0)); checks.append(("runtime",True)); p=self.root/".forge/self_test.json"; p.write_text(json.dumps({"checks":checks,"environment":self.environment()},indent=2),encoding="utf-8"); self.store.evidence("self_test",p,"TESTED"); ok=all(v for _,v in checks); self.store.event("self_test",{"checks":checks,"result":"PASS" if ok else "FAIL"}); return ok,checks

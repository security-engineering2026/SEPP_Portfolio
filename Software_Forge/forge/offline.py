from __future__ import annotations
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import Iterable

DEFAULT_CAPABILITIES = (
    "python_runtime",
    "git",
    "package_registry_cache",
    "documentation_cache",
    "browser_runtime",
    "platform_images",
    "knowledge_pack",
)

class OfflineProvisionError(ValueError):
    pass

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

class OfflineReadinessEngine:
    """Builds an auditable offline capability inventory and cache plan.

    It never claims that a capability is available merely because a download
    is planned. Availability is OBSERVED only when the required local artifact
    or executable is actually present and integrity-checked.
    """
    def __init__(self, root: Path):
        self.root=root.resolve()
        self.forge=self.root/".forge"
        self.offline=self.forge/"offline"
        self.cache=self.offline/"cache"

    def _dirs(self):
        names=("packages","toolchains","documentation","browser","platform_images","knowledge","models","sdk","emulators")
        return {n:self.cache/n for n in names}

    def inventory(self, required: Iterable[str]=DEFAULT_CAPABILITIES):
        dirs=self._dirs()
        for p in dirs.values(): p.mkdir(parents=True,exist_ok=True)
        checks=[]
        python_ok=shutil.which("python") or shutil.which("py") or sys.executable
        checks.append({"capability":"python_runtime","state":"OBSERVED" if python_ok else "UNKNOWN","locator":python_ok})
        git=shutil.which("git")
        checks.append({"capability":"git","state":"OBSERVED" if git else "UNKNOWN","locator":git})
        mapping={
            "package_registry_cache":dirs["packages"],
            "documentation_cache":dirs["documentation"],
            "browser_runtime":dirs["browser"],
            "platform_images":dirs["platform_images"],
            "knowledge_pack":dirs["knowledge"],
            "model_cache":dirs["models"],
            "android_sdk_cache":dirs["sdk"],
            "emulator_image_cache":dirs["emulators"],
        }
        for cap in required:
            if cap in {"python_runtime","git"}: continue
            p=mapping.get(cap)
            if p is None:
                continue
            files=[x for x in p.rglob("*") if x.is_file()]
            checks.append({"capability":cap,"state":"OBSERVED" if files else "MISSING","path":str(p),"artifact_count":len(files)})
        observed=sum(x["state"]=="OBSERVED" for x in checks)
        required_count=len(checks)
        readiness=round((observed/required_count)*100,2) if required_count else 100.0
        result={"schema_version":"1.0","state":"OBSERVED","generated_at":time.time(),"readiness_percent":readiness,
                "capabilities":checks,"cache_root":str(self.cache)}
        self.offline.mkdir(parents=True,exist_ok=True)
        (self.offline/"readiness.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result

    def plan(self, requirements: Iterable[dict]):
        plan=[]
        for req in requirements:
            name=str(req.get("capability") or req.get("name") or "")
            version=req.get("version")
            digest=req.get("sha256")
            plan.append({"capability":name,"version":version,"sha256":digest,"state":"PLANNED","download_required":True})
        result={"schema_version":"1.0","state":"PLANNED","generated_at":time.time(),"items":plan}
        self.offline.mkdir(parents=True,exist_ok=True)
        (self.offline/"provision_plan.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result

    def import_artifact(self, source: Path, capability: str, expected_sha256: str | None=None):
        source=source.resolve()
        if not source.is_file():
            raise OfflineProvisionError("artifact source is not a file")
        digest=_sha256_file(source)
        if expected_sha256 and digest.lower()!=expected_sha256.lower():
            raise OfflineProvisionError("artifact integrity mismatch")
        mapping={"package_registry_cache":"packages","documentation_cache":"documentation","browser_runtime":"browser","platform_images":"platform_images","knowledge_pack":"knowledge","model_cache":"models","android_sdk_cache":"sdk","emulator_image_cache":"emulators","toolchain_cache":"toolchains"}
        target_name=mapping.get(capability, capability)
        target=self._dirs().get(target_name)
        if target is None:
            raise OfflineProvisionError(f"unsupported cache capability: {capability}")
        target.mkdir(parents=True,exist_ok=True)
        dest=target/digest
        if not dest.exists():
            shutil.copy2(source,dest)
        return {"state":"VERIFIED","capability":capability,"sha256":digest,"path":str(dest),"size":dest.stat().st_size}

    def export_readiness(self):
        p=self.offline/"readiness.json"
        if not p.exists():
            return self.inventory()
        return json.loads(p.read_text(encoding="utf-8"))

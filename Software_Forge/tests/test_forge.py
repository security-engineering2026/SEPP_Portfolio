from pathlib import Path
import json, sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from forge.engine import ForgeEngine
from forge.manifest import ManifestEngine

def copy_manifest(tmp_path):
    src=Path(__file__).parents[1]/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.yaml"
    dst=tmp_path/"Software_Forge"; dst.mkdir(); (dst/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.yaml").write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

def test_persistence_and_self_test(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); ok,checks=e.self_test()
    assert ok and dict(checks)["persistence"] and dict(checks)["manifest"] and dict(checks)["requirements"]

def test_inventory(tmp_path):
    (tmp_path/"demo.py").write_text("print('ok')",encoding="utf-8"); assert ForgeEngine(tmp_path).inspect()["languages"]["Python"]==1

def test_manifest_requirement_traceability(tmp_path):
    copy_manifest(tmp_path); result=ManifestEngine(tmp_path).snapshot()
    assert result["manifest"]["state"]=="VERIFIED" and result["requirements"]["count"]>0

def test_independent_verification(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements()
    assert e.verify()["state"]=="VERIFIED"

def test_verifier_detects_forged_requirement_binding(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements()
    p=tmp_path/".forge/requirements.json"; graph=json.loads(p.read_text(encoding="utf-8")); graph["manifest_sha256"]="0"*64
    p.write_text(json.dumps(graph),encoding="utf-8")
    assert e.verify()["state"]=="FAILED"

def test_verifier_detects_tampered_evidence(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements()
    p=tmp_path/".forge/inventory.json"; p.write_text(p.read_text(encoding="utf-8")+"tamper",encoding="utf-8")
    assert e.verify()["state"]=="FAILED"

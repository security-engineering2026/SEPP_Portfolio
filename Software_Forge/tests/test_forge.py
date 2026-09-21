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
    p.write_text(json.dumps(graph),encoding="utf-8"); assert e.verify()["state"]=="FAILED"

def test_verifier_detects_tampered_evidence(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements()
    p=tmp_path/".forge/inventory.json"; p.write_text(p.read_text(encoding="utf-8")+"tamper",encoding="utf-8"); assert e.verify()["state"]=="FAILED"

def test_verifier_detects_tampered_event_chain(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements()
    import sqlite3
    con=sqlite3.connect(tmp_path/".forge/forge.db"); con.execute("UPDATE events SET payload=? WHERE id=(SELECT MIN(id) FROM events)", ('{"tampered":true}',)); con.commit(); con.close()
    result=e.verify(); assert result["state"]=="FAILED"; assert any(c["check"]=="event_chain_integrity" and not c["passed"] for c in result["checks"])

def test_build_engine_passes_source_compilation(tmp_path):
    copy_manifest(tmp_path); (tmp_path/"valid.py").write_text("value = 1\n", encoding="utf-8"); result=ForgeEngine(tmp_path).build(); assert result["state"]=="PASSED" and result["compiled_files"] >= 1

def test_build_engine_detects_syntax_failure(tmp_path):
    copy_manifest(tmp_path); (tmp_path/"broken.py").write_text("def broken(:\n", encoding="utf-8"); result=ForgeEngine(tmp_path).build(); assert result["state"]=="FAILED"; assert any("broken.py" in x["path"] for x in result["errors"])

def test_execution_success_persists_evidence(tmp_path):
    copy_manifest(tmp_path); result=ForgeEngine(tmp_path).execute([sys.executable,"-c","print('forge-execution-ok')"])
    assert result["state"]=="PASSED" and result["exit_code"]==0 and "forge-execution-ok" in result["stdout"]
    assert (tmp_path/".forge/execution.json").exists()

def test_execution_nonzero_exit_is_failure(tmp_path):
    copy_manifest(tmp_path); result=ForgeEngine(tmp_path).execute([sys.executable,"-c","import sys; print('failure-path'); sys.exit(7)"])
    assert result["state"]=="FAILED" and result["exit_code"]==7

def test_execution_timeout_is_failure(tmp_path):
    copy_manifest(tmp_path); result=ForgeEngine(tmp_path).execute([sys.executable,"-c","import time; time.sleep(2)"],timeout_seconds=0.1)
    assert result["state"]=="FAILED" and result["error"]=="TIMEOUT"

def test_execution_rejects_escape_cwd(tmp_path):
    copy_manifest(tmp_path)
    try:
        ForgeEngine(tmp_path).execute([sys.executable,"-c","print('no')"],cwd=tmp_path.parent)
    except ValueError as exc:
        assert "inside project root" in str(exc)
    else:
        assert False, "escape cwd must be rejected"

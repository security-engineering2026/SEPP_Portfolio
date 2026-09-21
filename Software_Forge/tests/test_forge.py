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


def test_verifier_detects_tampered_execution_record(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); e.inspect(); e.manifest(); e.requirements(); e.execute([sys.executable,"-c","print('binding')"])
    p=tmp_path/".forge/execution.json"; data=json.loads(p.read_text(encoding="utf-8")); data["stdout"]="forged"; p.write_text(json.dumps(data),encoding="utf-8")
    result=e.verify()
    assert result["state"]=="FAILED"
    assert any(c["check"].endswith("_identity") and not c["passed"] for c in result["checks"])


def test_failure_analyzer_classifies_timeout(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    result=e.analyze_failure({"state":"FAILED","error":"TIMEOUT","exit_code":None})
    assert result["state"]=="ANALYZED"
    assert result["category"]=="ENVIRONMENT"
    assert (tmp_path/".forge/failure.json").exists()

def test_failure_analyzer_classifies_os_error(tmp_path):
    copy_manifest(tmp_path)
    result=ForgeEngine(tmp_path).analyze_failure({"state":"FAILED","error":"OS_ERROR: process launch failed"})
    assert result["category"]=="OS"

def test_failure_analyzer_no_failure_is_explicit(tmp_path):
    copy_manifest(tmp_path)
    result=ForgeEngine(tmp_path).analyze_failure({"state":"PASSED","exit_code":0})
    assert result["state"]=="NO_FAILURE"
    assert result["category"] is None

def test_failure_analyzer_unknown_without_root_cause(tmp_path):
    copy_manifest(tmp_path)
    result=ForgeEngine(tmp_path).analyze_failure({"state":"FAILED","error":"something went wrong"})
    assert result["state"]=="ANALYZED"
    assert result["category"]=="UNKNOWN"
    assert result["confidence"]=="LOW"
    assert result["failure_id"]

def test_failure_analyzer_nonzero_exit_is_software_low_confidence(tmp_path):
    copy_manifest(tmp_path)
    result=ForgeEngine(tmp_path).analyze_failure({"state":"FAILED","exit_code":7})
    assert result["category"]=="SOFTWARE"
    assert result["confidence"]=="LOW"

def test_failure_analyzer_network_provider_hardware_signals(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    assert e.analyze_failure({"state":"FAILED","stderr":"DNS lookup failed"})["category"]=="NETWORK"
    assert e.analyze_failure({"state":"FAILED","stderr":"HTTP 429 RATE LIMIT"})["category"]=="PROVIDER"
    assert e.analyze_failure({"state":"FAILED","stderr":"NO SPACE LEFT ON DEVICE"})["category"]=="HARDWARE"

def test_failure_analyzer_binds_evidence_refs(tmp_path):
    copy_manifest(tmp_path)
    result=ForgeEngine(tmp_path).analyze_failure({
        "state":"FAILED","error":"OS_ERROR: launch",
        "execution_id":"exec-123","evidence_sha256":"abc123"
    })
    assert {x["field"] for x in result["evidence_refs"]}=={"execution_id","evidence_sha256"}

def test_failure_attempt_ledger_persists_analysis(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    result=e.analyze_failure({"state":"FAILED","error":"OS_ERROR: launch"})
    attempts=e.store.failure_attempts(result["failure_id"])
    assert len(attempts)==1
    assert attempts[0]["failure_id"]==result["failure_id"]
    assert attempts[0]["strategy"]=="deterministic_failure_analysis"
    assert attempts[0]["status"]=="ANALYZED"

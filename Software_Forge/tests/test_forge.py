from pathlib import Path
import json, sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from forge.engine import ForgeEngine
from forge.manifest import ManifestEngine

def copy_manifest(tmp_path):
    src=Path(__file__).parents[1]/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.4.yaml"
    dst=tmp_path/"Software_Forge"; dst.mkdir(); (dst/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.2.yaml").write_text(src.read_text(encoding="utf-8"),encoding="utf-8")

def test_persistence_and_self_test(tmp_path):
    copy_manifest(tmp_path); e=ForgeEngine(tmp_path); ok,checks=e.self_test()
    assert ok and dict(checks)["persistence"] and dict(checks)["manifest"] and dict(checks)["requirements"]

def test_inventory(tmp_path):
    (tmp_path/"demo.py").write_text("print('ok')",encoding="utf-8"); assert ForgeEngine(tmp_path).inspect()["languages"]["Python"]==1

def test_manifest_requirement_traceability(tmp_path):
    copy_manifest(tmp_path); result=ManifestEngine(tmp_path).snapshot()
    assert result["manifest"]["state"]=="VERIFIED" and result["requirements"]["count"]>0
    assert result["manifest"]["errors"]==[]

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

def test_verifier_detects_tampered_failure_attempt_details(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    result=e.analyze_failure({"state":"FAILED","error":"OS_ERROR: launch"})
    import sqlite3
    con=sqlite3.connect(tmp_path/".forge/forge.db")
    con.execute("UPDATE failure_attempts SET details=? WHERE id=1", ('{"category":"FORGED"}',))
    con.commit(); con.close()
    verification=e.verify()
    assert verification["state"]=="FAILED"
    assert any(c["check"]=="failure_attempt_1_binding" and not c["passed"] for c in verification["checks"])

def test_verifier_detects_forged_failure_attempt_event(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    e.analyze_failure({"state":"FAILED","error":"OS_ERROR: launch"})
    import sqlite3
    con=sqlite3.connect(tmp_path/".forge/forge.db")
    con.execute("UPDATE events SET payload=? WHERE kind='failure_attempt'", ('{"attempt_id":1,"failure_id":"forged","strategy":"deterministic_failure_analysis","status":"ANALYZED","details_sha256":"0"*64}',))
    con.commit(); con.close()
    verification=e.verify()
    assert verification["state"]=="FAILED"
    assert any(c["check"]=="failure_attempt_1_binding" and not c["passed"] for c in verification["checks"])

def test_checkpoint_restore_round_trip(tmp_path):
    copy_manifest(tmp_path)
    target=tmp_path/"app.py"; target.write_text("version = 'one'\n",encoding="utf-8")
    e=ForgeEngine(tmp_path)
    checkpoint=e.checkpoint("before-change")
    assert checkpoint["archive_sha256"]
    target.write_text("version = 'two'\n",encoding="utf-8")
    result=e.restore_checkpoint(checkpoint["checkpoint_id"])
    assert result["state"]=="RESTORED"
    assert target.read_text(encoding="utf-8")=="version = 'one'\n"

def test_checkpoint_detects_metadata_tamper(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    checkpoint=e.checkpoint("tamper")
    p=tmp_path/".forge/checkpoints"/checkpoint["checkpoint_id"]/"checkpoint.json"
    data=json.loads(p.read_text(encoding="utf-8")); data["tree_sha256"]="0"*64
    p.write_text(json.dumps(data),encoding="utf-8")
    try:
        e.restore_checkpoint(checkpoint["checkpoint_id"])
    except ValueError as exc:
        assert "integrity" in str(exc)
    else:
        assert False, "tampered checkpoint metadata must be rejected"

def test_checkpoint_detects_archive_tamper(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    checkpoint=e.checkpoint("archive-tamper")
    archive=tmp_path/".forge/checkpoints"/checkpoint["checkpoint_id"]/"source.zip"
    with archive.open("ab") as f:
        f.write(b"tampered")
    try:
        e.restore_checkpoint(checkpoint["checkpoint_id"])
    except ValueError as exc:
        assert "archive integrity" in str(exc)
    else:
        assert False, "tampered archive must be rejected"

def test_verifier_detects_checkpoint_tamper(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    e.manifest()
    e.requirements()
    e.checkpoint("verify")
    result=e.verify()
    assert result["state"]=="VERIFIED", result["checks"]
    checkpoint_root=tmp_path/".forge/checkpoints"
    checkpoint=next(p for p in checkpoint_root.iterdir() if p.is_dir())
    archive=checkpoint/"source.zip"
    with archive.open("ab") as f:
        f.write(b"tampered")
    result=e.verify()
    assert result["state"]=="FAILED"
    assert any(c["check"]=="checkpoint_integrity" and not c["passed"] for c in result["checks"])

def test_checkpoint_rejects_archive_path_traversal(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    checkpoint=e.checkpoint("archive")
    import zipfile
    archive=tmp_path/".forge/checkpoints"/checkpoint["checkpoint_id"]/"source.zip"
    with zipfile.ZipFile(archive,"a") as z:
        z.writestr("../escape.txt","forged")
    try:
        e.restore_checkpoint(checkpoint["checkpoint_id"])
    except ValueError as exc:
        assert "archive integrity" in str(exc)
    else:
        assert False, "unsafe archive path must be rejected"


def test_repair_applies_valid_patch_transactionally(tmp_path):
    copy_manifest(tmp_path)
    target=tmp_path/"app.py"
    target.write_text("value = 1\n", encoding="utf-8")
    result=ForgeEngine(tmp_path).repair(
        [{"path":"app.py","content":"value = 2\n"}],
        strategy="valid_patch",
    )
    assert result["state"]=="APPLIED"
    assert target.read_text(encoding="utf-8")=="value = 2\n"
    assert result["build"]["state"]=="PASSED"

def test_repair_rolls_back_failed_build(tmp_path):
    copy_manifest(tmp_path)
    target=tmp_path/"app.py"
    target.write_text("value = 1\n", encoding="utf-8")
    result=ForgeEngine(tmp_path).repair(
        [{"path":"app.py","content":"def broken(:\n"}],
        strategy="broken_patch",
    )
    assert result["state"]=="ROLLED_BACK"
    assert target.read_text(encoding="utf-8")=="value = 1\n"
    assert result["build"]["state"]=="FAILED"

def test_repair_rejects_protected_paths(tmp_path):
    copy_manifest(tmp_path)
    try:
        ForgeEngine(tmp_path).repair(
            [{"path":".forge/forbidden.txt","content":"x"}],
            strategy="protected_path",
        )
    except ValueError as exc:
        assert "protected project state" in str(exc)
    else:
        assert False, "repair must reject protected state"


def test_manifest_v13_offline_and_evolution_contract_is_verified(tmp_path):
    copy_manifest(tmp_path)
    result=ManifestEngine(tmp_path).snapshot()
    assert result["manifest"]["state"]=="VERIFIED", result["manifest"]["errors"]
    assert result["requirements"]["count"] >= 50


def test_offline_readiness_creates_local_capability_inventory(tmp_path):
    copy_manifest(tmp_path)
    from forge.offline import OfflineReadinessEngine
    result=OfflineReadinessEngine(tmp_path).inventory()
    assert result["state"]=="OBSERVED"
    assert (tmp_path/".forge/offline/readiness.json").exists()
    assert any(x["capability"]=="python_runtime" and x["state"]=="OBSERVED" for x in result["capabilities"])

def test_offline_artifact_import_is_content_addressed_and_verified(tmp_path):
    copy_manifest(tmp_path)
    from forge.offline import OfflineReadinessEngine
    source=tmp_path/"artifact.bin"; source.write_bytes(b"offline-artifact")
    result=OfflineReadinessEngine(tmp_path).import_artifact(source,"documentation_cache")
    assert result["state"]=="VERIFIED"
    assert Path(result["path"]).exists()
    assert result["sha256"]

def test_product_search_builds_large_deduplicated_pool(tmp_path):
    copy_manifest(tmp_path)
    from forge.product_intelligence_search import LocalCatalogSource, ProductSearchEngine
    records=[
        {"url":"https://example.test/a","name":"Forge A","description":"workflow automation build testing","capabilities":["build","test"],"source":"catalog-a"},
        {"url":"https://example.test/a","name":"Forge A duplicate","description":"build testing","capabilities":["build"],"source":"catalog-b"},
    ]
    for i in range(120):
        records.append({"url":f"https://example.test/{i}","name":f"Product {i}","description":"software lifecycle build test workflow","capabilities":["build","test"],"source":"catalog"})
    result=ProductSearchEngine([LocalCatalogSource(records)]).discover(
        ["software lifecycle","build test","workflow"], minimum_candidates=100
    )
    assert result["unique_count"]>=100
    assert result["unique_count"]==len(result["candidates"])
    assert result["minimum_met"] is True


def test_manifest_evolution_proposal_is_non_mutating(tmp_path):
    copy_manifest(tmp_path)
    from forge.manifest_evolution import ManifestEvolutionEngine
    e=ManifestEvolutionEngine(tmp_path)
    before=e._file_sha(e.manifest_path)
    proposal=e.propose(
        "Add an explicit offline knowledge cache requirement.",
        [{"op":"ADD","path":"offline.knowledge_graph_cache","value":"required"}],
        reason="speed and offline continuity",
    )
    assert proposal["approval_state"]=="PENDING"
    assert proposal["proposed_version"]=="1.4"
    assert e._file_sha(e.manifest_path)==before
    assert proposal["impact"]["regression_required"] is True
    assert proposal["changes"]

def test_manifest_evolution_requires_exact_approval_and_applies_versioned_change(tmp_path):
    copy_manifest(tmp_path)
    from forge.manifest_evolution import ManifestEvolutionEngine
    e=ManifestEvolutionEngine(tmp_path)
    proposal=e.propose(
        "Add local artifact index.",
        [{"op":"ADD","path":"offline.local_artifact_index","value":"required"}],
    )
    try:
        e.approve_and_apply(proposal["proposal_id"],"wrong-token")
    except ValueError as exc:
        assert "approval token" in str(exc)
    else:
        assert False, "wrong approval must be rejected"
    applied=e.approve_and_apply(proposal["proposal_id"],proposal["approval_token"])
    assert applied["approval_state"]=="APPROVED_APPLIED"
    assert applied["result_manifest_sha256"]
    assert Path(applied["result_manifest"]).exists()
    latest=ManifestEngine(tmp_path).snapshot()
    assert latest["manifest"]["state"]=="VERIFIED", latest["manifest"]["errors"]
    assert latest["manifest"]["path"].endswith("v1.4.yaml")
    ledger=json.loads((tmp_path/".forge/approval_ledger.json").read_text(encoding="utf-8"))
    assert ledger[-1]["proposal_id"]==proposal["proposal_id"]

def test_manifest_evolution_rejects_stale_manifest(tmp_path):
    copy_manifest(tmp_path)
    from forge.manifest_evolution import ManifestEvolutionEngine
    e=ManifestEvolutionEngine(tmp_path)
    proposal=e.propose("Add a cache.", [{"op":"ADD","path":"offline.extra_cache","value":"required"}])
    e.manifest_path.write_text(e.manifest_path.read_text(encoding="utf-8")+"\n",encoding="utf-8")
    try:
        e.approve_and_apply(proposal["proposal_id"],proposal["approval_token"])
    except ValueError as exc:
        assert "changed since proposal" in str(exc)
    else:
        assert False, "stale manifest must be rejected"

def test_manifest_evolution_removal_requires_explicit_approval(tmp_path):
    copy_manifest(tmp_path)
    from forge.manifest_evolution import ManifestEvolutionEngine
    e=ManifestEvolutionEngine(tmp_path)
    proposal=e.propose("Remove a requirement explicitly.", [{"op":"REMOVE","path":"offline.model_cache"}])
    assert any(c["op"]=="REMOVE" for c in proposal["changes"])
    assert proposal["approval_required"] is True


def test_change_impact_builds_regression_plan(tmp_path):
    copy_manifest(tmp_path)
    e=ForgeEngine(tmp_path)
    e.manifest()
    e.requirements()
    result=e.impact(["Software_Forge/forge/manifest.py"],["offline.local_build"])
    assert result["state"]=="OBSERVED"
    assert result["regression_required"] is True
    assert result["release_blocked_until_affected_tests_verified"] is True
    assert result["affected_requirement_ids"]
    assert result["affected_test_ids"]
    assert (tmp_path/".forge/impact.json").exists()

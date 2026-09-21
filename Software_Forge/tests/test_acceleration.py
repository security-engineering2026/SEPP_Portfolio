from pathlib import Path
import json
import sys
import pytest
sys.path.insert(0, str(Path(__file__).parents[1]))
from forge.acceleration import ExecutionAccelerationEngine, WorkUnit, AccelerationPlanError

def test_acceleration_parallel_batches_preserve_integration_gate(tmp_path):
    result=ExecutionAccelerationEngine(tmp_path).plan([
        WorkUnit("A","manifest",fast_gate=("manifest_validation",)),
        WorkUnit("B","inventory",fast_gate=("inventory_validation",)),
        WorkUnit("C","tests",depends_on=("A",),fast_gate=("targeted_tests",)),
        WorkUnit("D","integration",depends_on=("B","C"),fast_gate=("full_regression",)),
    ],max_parallel=2)
    assert result["state"]=="OBSERVED"
    assert result["batches"]==[["A","B"],["C"],["D"]]
    assert result["quality_preserved"] is True
    assert result["full_integration_gate_required"] is True
    assert result["independent_verification_required"] is True
    assert result["release_gate_cannot_be_bypassed"] is True
    assert (tmp_path/".forge"/"acceleration_plan.json").exists()

def test_acceleration_rejects_dependency_cycle(tmp_path):
    with pytest.raises(AccelerationPlanError,match="cyclic"):
        ExecutionAccelerationEngine(tmp_path).plan([WorkUnit("A","a",depends_on=("B",)),WorkUnit("B","b",depends_on=("A",))])

def test_acceleration_rejects_unknown_dependency(tmp_path):
    with pytest.raises(AccelerationPlanError,match="unknown"):
        ExecutionAccelerationEngine(tmp_path).plan([WorkUnit("A","a",depends_on=("MISSING",))])

def test_acceleration_plan_from_changes_creates_parallel_fast_gates(tmp_path):
    result=ExecutionAccelerationEngine(tmp_path).plan_from_changes(["src/a.cs","src/b.cs","tests/a_test.cs"],max_parallel=3)
    assert len(result["batches"][0])==3
    assert len(result["batches"][-1])==1
    assert "full_regression" in result["fast_gates"]
    assert "independent_verification" in result["fast_gates"]
    saved=json.loads((tmp_path/".forge"/"acceleration_plan.json").read_text(encoding="utf-8"))
    assert saved["plan_id"]==result["plan_id"]

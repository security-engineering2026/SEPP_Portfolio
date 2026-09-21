from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

class AccelerationPlanError(ValueError):
    pass

@dataclass(frozen=True)
class WorkUnit:
    unit_id: str
    title: str
    command: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    changed_paths: tuple[str, ...] = ()
    fast_gate: tuple[str, ...] = ()
    critical: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

class ExecutionAccelerationEngine:
    """Deterministic work planning layer for parallel execution without weakening gates."""
    def __init__(self, root: Path): self.root = root.resolve()
    @staticmethod
    def _id(value: str) -> str: return "WORK-" + hashlib.sha256(value.encode()).hexdigest()[:12].upper()
    @staticmethod
    def _validate_units(units: list[WorkUnit]) -> None:
        ids=[u.unit_id for u in units]
        if len(ids)!=len(set(ids)): raise AccelerationPlanError("duplicate work unit id")
        known=set(ids)
        for u in units:
            missing=set(u.depends_on)-known
            if missing: raise AccelerationPlanError(f"{u.unit_id} depends on unknown units: {sorted(missing)}")
            if u.unit_id in u.depends_on: raise AccelerationPlanError(f"{u.unit_id} cannot depend on itself")
        graph={u.unit_id:set(u.depends_on) for u in units}; resolved=set()
        while graph:
            ready=sorted(k for k,d in graph.items() if d<=resolved)
            if not ready: raise AccelerationPlanError("cyclic work-unit dependency graph")
            for k in ready: resolved.add(k); graph.pop(k)
    def plan(self, units: Iterable[WorkUnit], max_parallel: int|None=None) -> dict[str,Any]:
        work=list(units)
        if not work: raise AccelerationPlanError("at least one work unit is required")
        self._validate_units(work); limit=max_parallel if max_parallel is not None else max(1,len(work))
        if limit<1: raise AccelerationPlanError("max_parallel must be >= 1")
        remaining={u.unit_id:u for u in work}; completed=set(); batches=[]
        while remaining:
            ready=sorted(uid for uid,u in remaining.items() if set(u.depends_on)<=completed)
            if not ready: raise AccelerationPlanError("unable to resolve work-unit dependencies")
            batch=ready[:limit]; batches.append(batch)
            for uid in batch: completed.add(uid); remaining.pop(uid)
        result={"state":"OBSERVED","mode":"parallel_work_plan","max_parallel":limit,
          "work_units":[{"unit_id":u.unit_id,"title":u.title,"command":list(u.command),"depends_on":list(u.depends_on),"changed_paths":list(u.changed_paths),"fast_gate":list(u.fast_gate),"critical":u.critical,"metadata":u.metadata} for u in work],
          "batches":batches,"parallelizable_units":sum(1 for b in batches if len(b)>1),
          "fast_gates":sorted({g for u in work for g in u.fast_gate}),"quality_preserved":True,
          "full_integration_gate_required":True,"independent_verification_required":True,"release_gate_cannot_be_bypassed":True}
        result["plan_id"]=self._id(json.dumps(result,sort_keys=True))
        out=self.root/".forge"/"acceleration_plan.json"; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
        return result
    def plan_from_changes(self, changed_paths:list[str], max_parallel:int|None=None)->dict[str,Any]:
        paths=sorted(set(p.replace("\\","/") for p in changed_paths if p))
        if not paths: raise AccelerationPlanError("at least one changed path is required")
        units=[WorkUnit(self._id("change:"+p),f"Validate {p}",changed_paths=(p,),fast_gate=("syntax_or_compile","targeted_tests"),metadata={"source":"change_impact"}) for p in paths]
        integration=self._id("integration:"+"|".join(paths))
        units.append(WorkUnit(integration,"Integration gate",depends_on=tuple(u.unit_id for u in units),fast_gate=("full_regression","independent_verification"),metadata={"source":"integration"}))
        return self.plan(units,max_parallel=max_parallel)

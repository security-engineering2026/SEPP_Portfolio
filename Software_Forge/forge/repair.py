from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

from .build import BuildEngine
from .checkpoint import CheckpointEngine
from .store import ForgeStore

class RepairError(ValueError):
    pass

class RepairEngine:
    """Applies candidate text patches transactionally and rolls back failed candidates."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.store = ForgeStore(self.root)
        self.checkpoints = CheckpointEngine(self.root)

    def _failure_id(self, strategy: str, result: dict) -> str:
        payload = json.dumps({"strategy": strategy, "result": result}, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()

    def _safe_path(self, relative: str) -> Path:
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
            raise RepairError("patch path must be a relative project path")
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise RepairError("patch path must remain inside project root")
        if any(part in {".git", ".forge"} for part in path.relative_to(self.root).parts):
            raise RepairError("patch cannot modify protected project state")
        return path

    def _apply_files(self, files):
        if not isinstance(files, list) or not files:
            raise RepairError("patch files must be a non-empty list")
        prepared=[]
        seen=set()
        for item in files:
            if not isinstance(item, dict) or "path" not in item or "content" not in item:
                raise RepairError("each patch file requires path and content")
            path=self._safe_path(item["path"])
            rel=path.relative_to(self.root).as_posix()
            if rel in seen:
                raise RepairError(f"duplicate patch path: {rel}")
            seen.add(rel)
            if not isinstance(item["content"], str):
                raise RepairError("patch content must be text")
            prepared.append((path,item["content"]))
        originals={}
        for path,_ in prepared:
            originals[path] = path.read_text(encoding="utf-8") if path.exists() else None
        for path,content in prepared:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp=path.with_name(path.name + ".forge-patch.tmp")
            tmp.write_text(content, encoding="utf-8")
            os.replace(tmp, path)
        return originals

    def apply(self, files, strategy="candidate_patch", build=True):
        checkpoint=self.checkpoints.create(f"repair-{strategy}")
        self.store.evidence("repair_checkpoint", checkpoint["archive"], "TESTED")
        self.store.event("repair_checkpoint", {
            "checkpoint_id": checkpoint["checkpoint_id"],
            "strategy": strategy,
            "tree_sha256": checkpoint["tree_sha256"],
        })
        try:
            self._apply_files(files)
            build_result = BuildEngine(self.root).build() if build else {"state":"SKIPPED"}
            if build_result["state"] != "PASSED":
                failure_id=self._failure_id(strategy, build_result)
                self.store.failure_attempt(failure_id, strategy, "ROLLED_BACK", {
                    "phase":"build",
                    "build_state":build_result["state"],
                    "checkpoint_id":checkpoint["checkpoint_id"],
                })
                restored=self.checkpoints.restore(checkpoint["checkpoint_id"])
                self.store.event("repair_rollback", {
                    "checkpoint_id":checkpoint["checkpoint_id"],
                    "failure_id":failure_id,
                    "reason":"build_failed",
                    "restored":restored["state"],
                })
                return {
                    "state":"ROLLED_BACK",
                    "strategy":strategy,
                    "checkpoint_id":checkpoint["checkpoint_id"],
                    "failure_id":failure_id,
                    "build":build_result,
                }
            self.store.failure_attempt(
                self._failure_id(strategy, build_result),
                strategy,
                "APPLIED",
                {"phase":"build","build_state":build_result["state"],"checkpoint_id":checkpoint["checkpoint_id"]},
            )
            self.store.event("repair_applied", {
                "checkpoint_id":checkpoint["checkpoint_id"],
                "strategy":strategy,
                "build_state":build_result["state"],
            })
            return {
                "state":"APPLIED",
                "strategy":strategy,
                "checkpoint_id":checkpoint["checkpoint_id"],
                "build":build_result,
            }
        except Exception as exc:
            failure_id=self._failure_id(strategy, {"error":str(exc)})
            try:
                restored=self.checkpoints.restore(checkpoint["checkpoint_id"])
                rollback_state=restored["state"]
            except Exception as rollback_exc:
                rollback_state=f"FAILED:{rollback_exc}"
            self.store.failure_attempt(failure_id, strategy, "ROLLED_BACK" if rollback_state=="RESTORED" else "ROLLBACK_FAILED", {
                "phase":"exception",
                "error":str(exc),
                "checkpoint_id":checkpoint["checkpoint_id"],
                "rollback_state":rollback_state,
            })
            self.store.event("repair_exception", {
                "checkpoint_id":checkpoint["checkpoint_id"],
                "failure_id":failure_id,
                "rollback_state":rollback_state,
            })
            if rollback_state != "RESTORED":
                raise RepairError(f"repair failed and rollback failed: {exc}; {rollback_state}") from exc
            return {
                "state":"ROLLED_BACK",
                "strategy":strategy,
                "checkpoint_id":checkpoint["checkpoint_id"],
                "failure_id":failure_id,
                "error":str(exc),
            }

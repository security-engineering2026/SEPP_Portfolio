from __future__ import annotations

import copy
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import yaml


class ManifestEvolutionError(ValueError):
    pass


class ManifestEvolutionEngine:
    """Propose and explicitly apply auditable Product Contract changes."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.manifest_path = self._find_manifest()
        self.history_dir = self.root / ".forge" / "manifest_history"
        self.approval_path = self.root / ".forge" / "approval_ledger.json"

    def _find_manifest(self) -> Path:
        candidates = sorted(
            [
                *self.root.glob("Software_Forge/SOFTWARE_FORGE_MASTER_MANIFEST_v*.yaml"),
                *self.root.glob("SOFTWARE_FORGE_MASTER_MANIFEST_v*.yaml"),
                *self.root.glob("FORGE_MANIFEST.yaml"),
            ],
            key=lambda p: self._version_key(p),
            reverse=True,
        )
        if not candidates:
            raise ManifestEvolutionError("Manifest not found")
        return candidates[0]

    @staticmethod
    def _version_key(path: Path):
        import re
        m = re.search(r"_v(\d+)\.(\d+)\.yaml$", path.name)
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)

    def _load(self) -> dict[str, Any]:
        data = yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ManifestEvolutionError("Manifest root must be a mapping")
        return data

    @staticmethod
    def _sha(data: Any) -> str:
        raw = yaml.safe_dump(data, sort_keys=True, allow_unicode=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _file_sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def _next_version(version: str) -> str:
        major, minor = (int(x) for x in str(version).split(".", 1))
        return f"{major}.{minor + 1}"

    @staticmethod
    def _diff(old: Any, new: Any, path: str = "") -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        if isinstance(old, dict) and isinstance(new, dict):
            for key in sorted(set(old) | set(new)):
                p = f"{path}.{key}" if path else key
                if key not in old:
                    changes.append({"op": "ADD", "path": p, "old": None, "new": new[key]})
                elif key not in new:
                    changes.append({"op": "REMOVE", "path": p, "old": old[key], "new": None})
                else:
                    changes.extend(ManifestEvolutionEngine._diff(old[key], new[key], p))
            return changes
        if isinstance(old, list) and isinstance(new, list):
            if old != new:
                changes.append({"op": "MODIFY", "path": path, "old": old, "new": new})
            return changes
        if old != new:
            changes.append({"op": "MODIFY", "path": path, "old": old, "new": new})
        return changes

    @staticmethod
    def _get_path(data: dict[str, Any], dotted: str):
        cur: Any = data
        for part in dotted.split("."):
            if not isinstance(cur, dict) or part not in cur:
                raise ManifestEvolutionError(f"Unknown manifest path: {dotted}")
            cur = cur[part]
        return cur

    @staticmethod
    def _set_path(data: dict[str, Any], dotted: str, value: Any, remove: bool = False):
        parts = dotted.split(".")
        cur: Any = data
        for part in parts[:-1]:
            if part not in cur or not isinstance(cur[part], dict):
                cur[part] = {}
            cur = cur[part]
        if remove:
            if parts[-1] not in cur:
                raise ManifestEvolutionError(f"Unknown manifest path: {dotted}")
            del cur[parts[-1]]
        else:
            cur[parts[-1]] = value

    def _validate_candidate(self, data: dict[str, Any]) -> None:
        version = data.get("forge_manifest_version")
        if not isinstance(version, str):
            raise ManifestEvolutionError("forge_manifest_version must be a string")
        if not isinstance(data.get("product"), dict):
            raise ManifestEvolutionError("product section is required")
        if not isinstance(data.get("validation"), dict):
            raise ManifestEvolutionError("validation section is required")
        if not isinstance(data.get("truth_states"), list):
            raise ManifestEvolutionError("truth_states section is required")

    def _impact(self, changes: list[dict[str, Any]]) -> dict[str, Any]:
        paths = [c["path"] for c in changes]
        affected_requirements = []
        affected_tests = []
        release_gates = []
        for p in paths:
            rid = "REQ-" + hashlib.sha1(p.encode()).hexdigest()[:10].upper()
            tid = "TEST-" + hashlib.sha1((rid + ":traceability").encode()).hexdigest()[:10].upper()
            affected_requirements.append(rid)
            affected_tests.append(tid)
            if any(x in p for x in ("release", "validation", "core_principles", "product_intelligence", "offline", "online_preprovisioning", "manifest_evolution")):
                release_gates.append(p)
        return {
            "changed_paths": paths,
            "affected_requirement_ids": sorted(set(affected_requirements)),
            "affected_test_ids": sorted(set(affected_tests)),
            "release_gate_paths": sorted(set(release_gates)),
            "regression_required": bool(changes),
        }

    def propose(self, user_instruction: str, changes: list[dict[str, Any]], reason: str = "", evidence_refs: list[str] | None = None) -> dict[str, Any]:
        if not user_instruction.strip():
            raise ManifestEvolutionError("explicit user instruction is required")
        if not changes:
            raise ManifestEvolutionError("at least one manifest change is required")
        current = self._load()
        candidate = copy.deepcopy(current)
        for change in changes:
            op = change.get("op", "MODIFY").upper()
            path = change.get("path")
            if not path:
                raise ManifestEvolutionError("each change requires path")
            if op == "REMOVE":
                self._set_path(candidate, path, None, remove=True)
            elif op in {"ADD", "MODIFY"}:
                self._set_path(candidate, path, change.get("value"))
            else:
                raise ManifestEvolutionError(f"unsupported operation: {op}")
        candidate["forge_manifest_version"] = self._next_version(current["forge_manifest_version"])
        self._validate_candidate(candidate)
        diff = self._diff(current, candidate)
        impact = self._impact(diff)
        proposal = {
            "proposal_id": "MCP-" + hashlib.sha256((self._sha(current) + user_instruction + json.dumps(diff, sort_keys=True)).encode()).hexdigest()[:16].upper(),
            "created_at": time.time(),
            "user_instruction": user_instruction,
            "reason": reason,
            "current_manifest": str(self.manifest_path),
            "current_manifest_sha256": self._file_sha(self.manifest_path),
            "current_contract_sha256": self._sha(current),
            "proposed_version": candidate["forge_manifest_version"],
            "proposed_contract_sha256": self._sha(candidate),
            "changes": diff,
            "impact": impact,
            "evidence_refs": evidence_refs or [],
            "approval_required": True,
            "approval_state": "PENDING",
        }
        proposal["approval_token"] = hashlib.sha256(
            (proposal["proposal_id"] + proposal["current_manifest_sha256"] + proposal["proposed_contract_sha256"]).encode()
        ).hexdigest()
        self.history_dir.mkdir(parents=True, exist_ok=True)
        path = self.history_dir / f"{proposal['proposal_id']}.proposal.json"
        path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
        return proposal

    def approve_and_apply(self, proposal_id: str, approval_token: str, approver: str = "local_user") -> dict[str, Any]:
        proposal_path = self.history_dir / f"{proposal_id}.proposal.json"
        if not proposal_path.exists():
            raise ManifestEvolutionError("proposal not found")
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        if proposal["approval_token"] != approval_token:
            raise ManifestEvolutionError("approval token mismatch")
        if proposal["approval_state"] != "PENDING":
            raise ManifestEvolutionError("proposal is not pending")
        if self._file_sha(self.manifest_path) != proposal["current_manifest_sha256"]:
            raise ManifestEvolutionError("current manifest changed since proposal; rebase required")

        current = self._load()
        candidate = copy.deepcopy(current)
        for change in proposal["changes"]:
            op = change["op"]
            if op == "REMOVE":
                self._set_path(candidate, change["path"], None, remove=True)
            else:
                self._set_path(candidate, change["path"], change["new"])
        self._validate_candidate(candidate)
        if self._sha(candidate) != proposal["proposed_contract_sha256"]:
            raise ManifestEvolutionError("proposal content hash mismatch")

        new_path = self.manifest_path.with_name(f"SOFTWARE_FORGE_MASTER_MANIFEST_v{proposal['proposed_version']}.yaml")
        if new_path.exists():
            raise ManifestEvolutionError("target manifest version already exists")
        new_path.write_text(yaml.safe_dump(candidate, sort_keys=False, allow_unicode=True), encoding="utf-8")

        applied = dict(proposal)
        applied.update({
            "approval_state": "APPROVED_APPLIED",
            "approved_at": time.time(),
            "approver": approver,
            "result_manifest": str(new_path),
            "result_manifest_sha256": self._file_sha(new_path),
        })
        (self.history_dir / f"{proposal_id}.applied.json").write_text(json.dumps(applied, indent=2, sort_keys=True), encoding="utf-8")

        ledger = []
        if self.approval_path.exists():
            ledger = json.loads(self.approval_path.read_text(encoding="utf-8"))
        ledger.append({
            "approval_id": "APP-" + proposal_id[4:],
            "proposal_id": proposal_id,
            "decision": "APPROVED_APPLIED",
            "approver": approver,
            "manifest_before_sha256": proposal["current_manifest_sha256"],
            "manifest_after_sha256": applied["result_manifest_sha256"],
            "proposal_sha256": hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
            "timestamp": applied["approved_at"],
        })
        self.approval_path.parent.mkdir(parents=True, exist_ok=True)
        self.approval_path.write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")
        return applied

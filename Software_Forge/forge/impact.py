from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ImpactAnalysisError(ValueError):
    pass


class ChangeImpactEngine:
    """Build a deterministic change -> requirement -> test regression plan."""

    def __init__(self, root: Path):
        self.root = root.resolve()

    @staticmethod
    def _id(prefix: str, value: str) -> str:
        return prefix + "-" + hashlib.sha1(value.encode()).hexdigest()[:10].upper()

    def _load_requirements(self) -> dict[str, Any]:
        p = self.root / ".forge" / "requirements.json"
        if not p.exists():
            return {"requirements": []}
        return json.loads(p.read_text(encoding="utf-8"))

    def analyze(self, changed_paths: list[str], manifest_paths: list[str] | None = None) -> dict[str, Any]:
        paths = sorted(set(changed_paths + (manifest_paths or [])))
        if not paths:
            raise ImpactAnalysisError("at least one changed path is required")
        graph = self._load_requirements()
        requirements = graph.get("requirements", [])
        affected = []
        tests = []
        components = set()

        for path in paths:
            normalized = path.replace("\\", "/")
            component = normalized.split("/")[-1].split(".")[0]
            components.add(component)
            direct = [r for r in requirements if r.get("manifest_path") == normalized]
            if not direct:
                direct = [r for r in requirements if any(token and token in r.get("manifest_path", "") for token in component.split("_"))]
            if not direct:
                rid = self._id("REQ", normalized)
                direct = [{"requirement_id": rid, "manifest_path": normalized, "status": "INFERRED", "tests": []}]
            for req in direct:
                affected.append(req["requirement_id"])
                bound = req.get("tests", [])
                if bound:
                    tests.extend(t.get("test_id") for t in bound if t.get("test_id"))
                else:
                    tests.append(self._id("TEST", req["requirement_id"] + ":regression"))

        affected = sorted(set(affected))
        tests = sorted(set(tests))
        result = {
            "state": "OBSERVED",
            "changed_paths": paths,
            "affected_components": sorted(components),
            "affected_requirement_ids": affected,
            "affected_test_ids": tests,
            "regression_required": True,
            "release_blocked_until_affected_tests_verified": True,
            "analysis_id": self._id("IMPACT", "|".join(paths) + "|" + "|".join(affected)),
        }
        out = self.root / ".forge" / "impact.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        return result

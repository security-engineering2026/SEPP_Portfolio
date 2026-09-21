from __future__ import annotations
import hashlib, json, time
from pathlib import Path

CATEGORIES = ("SOFTWARE", "ENVIRONMENT", "NETWORK", "PROVIDER", "OS", "HARDWARE", "UNKNOWN")

class FailureAnalyzer:
    """Deterministic, evidence-bounded failure classification; never invents a root cause."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.forge = self.root / ".forge"

    def analyze(self, observation: dict) -> dict:
        if not isinstance(observation, dict):
            raise ValueError("observation must be a mapping")
        state = str(observation.get("state", "")).upper()
        if state != "FAILED":
            result = {
                "analyzer": "deterministic_v2", "state": "NO_FAILURE",
                "failure_id": None, "category": None, "confidence": "NONE",
                "cause": "observed operation did not fail", "evidence_refs": [],
                "source_state": state, "timestamp": time.time(),
            }
            return self._persist(result)

        error_raw = str(observation.get("error") or "")
        stderr_raw = str(observation.get("stderr") or "")
        signal = (error_raw + "\n" + stderr_raw).upper()
        category, cause, confidence = "UNKNOWN", "insufficient evidence to classify root cause", "LOW"

        if "TIMEOUT" in signal:
            category, cause, confidence = "ENVIRONMENT", "execution exceeded configured timeout", "HIGH"
        elif error_raw.upper().startswith("OS_ERROR"):
            category, cause, confidence = "OS", "operating-system process launch failure", "HIGH"
        elif any(x in signal for x in ("CONNECTION", "NETWORK", "DNS", "SOCKET", "PROXY")):
            category, cause, confidence = "NETWORK", "network-related failure signal observed", "MEDIUM"
        elif any(x in signal for x in ("PROVIDER", "API KEY", "RATE LIMIT", "429")):
            category, cause, confidence = "PROVIDER", "external provider failure signal observed", "MEDIUM"
        elif any(x in signal for x in ("DISK FULL", "NO SPACE", "OUT OF MEMORY", "DEVICE")):
            category, cause, confidence = "HARDWARE", "resource or device failure signal observed", "MEDIUM"
        elif observation.get("exit_code") not in (None, 0):
            category, cause, confidence = "SOFTWARE", "command returned a non-zero exit code without a stronger environmental signal", "LOW"

        evidence_refs = []
        for key in ("execution_id", "evidence_sha256", "build_id"):
            if observation.get(key):
                evidence_refs.append({"field": key, "value": str(observation[key])})

        canonical = {
            "category": category, "cause": cause, "confidence": confidence,
            "source_state": state, "exit_code": observation.get("exit_code"),
            "error": observation.get("error"), "stderr": observation.get("stderr"),
            "evidence_refs": evidence_refs,
        }
        failure_id = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        result = {
            "analyzer": "deterministic_v2", "state": "ANALYZED",
            "failure_id": failure_id, "category": category, "confidence": confidence,
            "cause": cause, "evidence_refs": evidence_refs,
            "source_state": state, "exit_code": observation.get("exit_code"),
            "error": observation.get("error"), "timestamp": time.time(),
        }
        return self._persist(result)

    def _persist(self, result: dict) -> dict:
        self.forge.mkdir(parents=True, exist_ok=True)
        (self.forge / "failure.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

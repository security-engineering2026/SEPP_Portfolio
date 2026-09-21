from __future__ import annotations
import json, time
from pathlib import Path

CATEGORIES = ("SOFTWARE", "ENVIRONMENT", "NETWORK", "PROVIDER", "OS", "HARDWARE")

class FailureAnalyzer:
    """Deterministic failure classification from observed execution/build evidence."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.forge = self.root / ".forge"

    def analyze(self, observation: dict) -> dict:
        if not isinstance(observation, dict):
            raise ValueError("observation must be a mapping")
        state = str(observation.get("state", "")).upper()
        error = str(observation.get("error") or "").upper()
        stderr = str(observation.get("stderr") or "").upper()
        exit_code = observation.get("exit_code")
        category = "SOFTWARE"
        reason = "observed command/build failure"
        if "TIMEOUT" in error:
            category, reason = "ENVIRONMENT", "execution exceeded configured timeout"
        elif error.startswith("OS_ERROR"):
            category, reason = "OS", "operating-system process launch failure"
        elif any(x in error + stderr for x in ("CONNECTION", "NETWORK", "DNS", "SOCKET", "PROXY", "TIMEOUT")):
            category, reason = "NETWORK", "network-related failure signal observed"
        elif any(x in error + stderr for x in ("PROVIDER", "API KEY", "RATE LIMIT", "429")):
            category, reason = "PROVIDER", "external provider failure signal observed"
        elif any(x in error + stderr for x in ("DISK FULL", "NO SPACE", "OUT OF MEMORY", "DEVICE")):
            category, reason = "HARDWARE", "resource/device failure signal observed"
        result = {
            "analyzer": "deterministic_v1",
            "state": "ANALYZED" if state == "FAILED" else "NO_FAILURE",
            "category": category if state == "FAILED" else None,
            "reason": reason if state == "FAILED" else "observed operation did not fail",
            "source_state": state,
            "exit_code": exit_code,
            "error": observation.get("error"),
            "evidence": {"observation": observation},
            "timestamp": time.time(),
        }
        self.forge.mkdir(parents=True, exist_ok=True)
        (self.forge / "failure.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

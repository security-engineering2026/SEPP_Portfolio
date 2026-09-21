from __future__ import annotations
import json, py_compile, time
from pathlib import Path

class BuildEngine:
    """Deterministic source/build validation; never treats a planned command as a build result."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.forge = self.root / ".forge"

    def build(self) -> dict:
        started = time.time()
        errors = []
        compiled = 0
        for path in sorted(self.root.rglob("*.py")):
            if any(part in {".git", ".forge", "__pycache__"} for part in path.parts):
                continue
            try:
                py_compile.compile(str(path), doraise=True)
                compiled += 1
            except Exception as exc:
                errors.append({"path": str(path), "error": str(exc)})
        result = {
            "builder": "python_compile",
            "state": "PASSED" if not errors else "FAILED",
            "compiled_files": compiled,
            "errors": errors,
            "duration_seconds": round(time.time() - started, 6),
        }
        self.forge.mkdir(parents=True, exist_ok=True)
        (self.forge / "build.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

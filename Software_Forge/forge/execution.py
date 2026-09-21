from __future__ import annotations
import json, os, platform, subprocess, time
from pathlib import Path

class ExecutionEngine:
    """Controlled local execution with timeout, output capture and durable evidence."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.forge = self.root / ".forge"

    def run(self, command: list[str], timeout_seconds: float = 30.0, cwd: Path | None = None) -> dict:
        if not command or not all(isinstance(x, str) and x for x in command):
            raise ValueError("command must be a non-empty list of strings")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        workdir = (cwd or self.root).resolve()
        if not workdir.is_relative_to(self.root):
            raise ValueError("execution cwd must remain inside project root")
        started = time.time()
        state = "FAILED"
        exit_code = None
        stdout = ""
        stderr = ""
        error = None
        try:
            p = subprocess.run(command, cwd=workdir, capture_output=True, text=True,
                               timeout=timeout_seconds, shell=False, check=False)
            exit_code = p.returncode
            stdout, stderr = p.stdout, p.stderr
            state = "PASSED" if exit_code == 0 else "FAILED"
        except subprocess.TimeoutExpired as exc:
            state = "FAILED"
            error = "TIMEOUT"
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
        except OSError as exc:
            error = f"OS_ERROR:{exc}"
        result = {
            "state": state, "command": command, "cwd": str(workdir),
            "exit_code": exit_code, "stdout": stdout, "stderr": stderr,
            "error": error, "timeout_seconds": timeout_seconds,
            "duration_seconds": round(time.time() - started, 6),
            "environment": {"os": platform.platform(), "python": platform.python_version(), "pid": os.getpid()},
        }
        self.forge.mkdir(parents=True, exist_ok=True)
        (self.forge / "execution.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

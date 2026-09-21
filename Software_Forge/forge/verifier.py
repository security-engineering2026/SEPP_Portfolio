from __future__ import annotations
import hashlib, json, sqlite3
from pathlib import Path
from .manifest import ManifestEngine
from .store import ForgeStore

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _execution_id(data: dict) -> str:
    payload = {k: v for k, v in data.items() if k != "execution_id"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class IndependentVerifier:
    """Recomputes verification from source and persisted evidence; builder self-test is not authority."""
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.forge = self.root / ".forge"

    def verify(self) -> dict:
        checks = []
        manifest_candidates = (
            self.root / "SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.yaml",
            self.root / "FORGE_MANIFEST.yaml",
            self.root / "Software_Forge" / "SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.yaml",
            self.root / "Software_Forge" / "FORGE_MANIFEST.yaml",
            self.root.parent / "SOFTWARE_FORGE_MASTER_MANIFEST_v1.0.yaml",
        )
        manifest_path = next((p for p in manifest_candidates if p.exists()), None)
        if manifest_path is None:
            checks.append({"check":"manifest_present","passed":False,"reason":"manifest not found"})
            return self._write(checks, "BLOCKED")
        try:
            snap = ManifestEngine(self.root).snapshot()
            checks.append({"check":"manifest_recomputed","passed":snap["manifest"]["state"] == "VERIFIED"})
        except Exception as exc:
            checks.append({"check":"manifest_recomputed","passed":False,"reason":str(exc)})
            return self._write(checks, "FAILED")

        req_path = self.forge / "requirements.json"
        if not req_path.exists():
            checks.append({"check":"requirements_present","passed":False,"reason":"requirements graph not found"})
        else:
            try:
                graph = json.loads(req_path.read_text(encoding="utf-8"))
                expected = snap["manifest"]["sha256"]
                checks.append({"check":"manifest_binding","passed":graph.get("manifest_sha256") == expected})
                expected_ids = {r["id"] for r in snap["requirements"]["requirements"]}
                observed_ids = {r.get("requirement_id") for r in graph.get("requirements", [])}
                checks.append({"check":"requirement_set_binding","passed":expected_ids == observed_ids})
            except Exception as exc:
                checks.append({"check":"requirements_integrity","passed":False,"reason":str(exc)})

        chain = ForgeStore(self.root).verify_event_chain()
        checks.append({"check":"event_chain_integrity","passed":chain["state"] == "VERIFIED","details":chain})

        evidence_ok = True
        db = self.forge / "forge.db"
        if db.exists():
            con = sqlite3.connect(db)
            try:
                rows = con.execute("SELECT id,kind,path,sha256 FROM evidence ORDER BY id").fetchall()
                events = con.execute("SELECT payload FROM events WHERE kind='execution' ORDER BY id").fetchall()
            finally:
                con.close()
            execution_bindings = []
            for payload, in events:
                try: execution_bindings.append(json.loads(payload))
                except Exception: execution_bindings.append({})
            for eid, kind, raw_path, expected_hash in rows:
                p = Path(raw_path)
                try:
                    actual = _sha256(p)
                    ok = actual == expected_hash
                except Exception:
                    actual, ok = None, False
                evidence_ok = evidence_ok and ok
                checks.append({"check":f"evidence_{eid}_integrity","passed":ok,"expected":expected_hash,"observed":actual})
                if kind == "execution":
                    try:
                        data=json.loads(p.read_text(encoding="utf-8"))
                        recomputed=_execution_id(data)
                        identity_ok=data.get("execution_id")==recomputed
                        bound=any(b.get("execution_id")==data.get("execution_id") and b.get("evidence_sha256")==expected_hash for b in execution_bindings)
                        checks.append({"check":f"execution_{eid}_identity","passed":identity_ok,"execution_id":data.get("execution_id"),"recomputed":recomputed})
                        checks.append({"check":f"execution_{eid}_event_binding","passed":bound})
                        evidence_ok = evidence_ok and identity_ok and bound
                    except Exception as exc:
                        evidence_ok=False
                        checks.append({"check":f"execution_{eid}_binding","passed":False,"reason":str(exc)})
        checks.append({"check":"evidence_integrity","passed":evidence_ok})
        state = "VERIFIED" if checks and all(c["passed"] for c in checks) else "FAILED"
        return self._write(checks, state)

    def _write(self, checks, state):
        result = {"verifier":"independent","state":state,"checks":checks}
        result["verification_sha256"] = hashlib.sha256(json.dumps(result,sort_keys=True).encode()).hexdigest()
        out = self.forge / "verification.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2), encoding="utf-8")
        return result

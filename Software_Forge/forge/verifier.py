from __future__ import annotations
import hashlib, json, sqlite3, zipfile
from pathlib import Path
from .manifest import ManifestEngine
from .store import ForgeStore

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _execution_id(data: dict) -> str:
    payload = {k: v for k, v in data.items() if k != "execution_id"}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def _failure_attempt_details_sha256(details: str) -> str:
    try:
        canonical = json.dumps(json.loads(details), sort_keys=True, separators=(",", ":"))
    except Exception:
        canonical = details
    return hashlib.sha256(canonical.encode()).hexdigest()

def _canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()

def _checkpoint_identity(tree, manifest_hash, environment):
    return hashlib.sha256(_canonical({
        "tree": tree,
        "manifest_sha256": manifest_hash,
        "environment": environment,
    })).hexdigest()

def _archive_tree(archive: Path):
    entries=[]
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name=Path(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise ValueError("unsafe checkpoint archive path")
            data=z.read(info)
            entries.append({
                "path": info.filename.replace("\\", "/"),
                "sha256": hashlib.sha256(data).hexdigest(),
                "size": len(data),
            })
    return sorted(entries, key=lambda x: x["path"])

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

        checkpoint_ok = True
        checkpoint_root = self.forge / "checkpoints"
        if checkpoint_root.exists():
            for target in sorted(p for p in checkpoint_root.iterdir() if p.is_dir()):
                record_path = target / "checkpoint.json"
                archive = target / "source.zip"
                check_name = target.name
                try:
                    record = json.loads(record_path.read_text(encoding="utf-8"))
                    archive_hash = _sha256(archive)
                    archive_hash_ok = record.get("archive_sha256") == archive_hash
                    tree_hash_ok = hashlib.sha256(_canonical(record["tree"])).hexdigest() == record.get("tree_sha256")
                    identity_ok = record.get("identity_sha256") == _checkpoint_identity(
                        record["tree"], record.get("manifest_sha256"), record.get("environment")
                    )
                    archive_tree = _archive_tree(archive)
                    archive_content_ok = archive_tree == sorted(record["tree"], key=lambda x: x["path"])
                    checks.extend([
                        {"check":f"checkpoint_{check_name}_archive_hash","passed":archive_hash_ok},
                        {"check":f"checkpoint_{check_name}_tree_hash","passed":tree_hash_ok},
                        {"check":f"checkpoint_{check_name}_identity","passed":identity_ok},
                        {"check":f"checkpoint_{check_name}_archive_content","passed":archive_content_ok},
                    ])
                    checkpoint_ok = checkpoint_ok and archive_hash_ok and tree_hash_ok and identity_ok and archive_content_ok
                except Exception as exc:
                    checkpoint_ok = False
                    checks.append({"check":f"checkpoint_{check_name}_integrity","passed":False,"reason":str(exc)})
        checks.append({"check":"checkpoint_integrity","passed":checkpoint_ok})

        evidence_ok = True
        db = self.forge / "forge.db"
        if db.exists():
            con = sqlite3.connect(db)
            try:
                rows = con.execute("SELECT id,kind,path,sha256 FROM evidence ORDER BY id").fetchall()
                events = con.execute("SELECT payload FROM events WHERE kind='execution' ORDER BY id").fetchall()
                attempt_rows = con.execute("SELECT id,failure_id,strategy,status,details FROM failure_attempts ORDER BY id").fetchall()
                attempt_events = con.execute("SELECT payload FROM events WHERE kind='failure_attempt' ORDER BY id").fetchall()
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
            event_map = {}
            for payload in attempt_events:
                try:
                    item=json.loads(payload); event_map[item.get("attempt_id")]=item
                except Exception:
                    pass
            for aid, failure_id, strategy, status, details in attempt_rows:
                details_hash = _failure_attempt_details_sha256(details)
                event = event_map.get(aid)
                ok = bool(event and event.get("failure_id")==failure_id and event.get("strategy")==strategy and event.get("status")==status and event.get("details_sha256")==details_hash)
                checks.append({"check":f"failure_attempt_{aid}_binding","passed":ok,"details_sha256":details_hash})
                evidence_ok = evidence_ok and ok
            checks.append({"check":"failure_attempt_ledger_integrity","passed":all(c["passed"] for c in checks if c["check"].startswith("failure_attempt_"))})
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

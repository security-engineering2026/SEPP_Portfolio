from __future__ import annotations
import hashlib, json, platform, shutil, time, zipfile
from pathlib import Path

EXCLUDED = {".git", ".forge", "__pycache__"}

def _canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode()

def _file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _tree(root: Path):
    items=[]
    for p in sorted(root.rglob("*")):
        if not p.is_file() or any(part in EXCLUDED for part in p.relative_to(root).parts):
            continue
        rel=p.relative_to(root).as_posix()
        items.append({"path":rel,"sha256":_file_hash(p),"size":p.stat().st_size})
    return items

class CheckpointError(ValueError):
    pass

class CheckpointEngine:
    """Creates and restores source checkpoints with deterministic tree and archive identity."""
    def __init__(self, root: Path):
        self.root=root.resolve()
        self.forge=self.root/".forge"
        self.base=self.forge/"checkpoints"

    def _environment(self):
        return {"os":platform.platform(),"python":platform.python_version(),"machine":platform.machine()}

    def _manifest_hash(self):
        for p in (
            self.root/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.2.yaml",
            self.root/"Software_Forge"/"SOFTWARE_FORGE_MASTER_MANIFEST_v1.2.yaml",
            self.root/"FORGE_MANIFEST.yaml",
        ):
            if p.exists():
                return _file_hash(p)
        return None

    def _identity(self, tree, manifest_hash, environment=None):
        payload={"tree":tree,"manifest_sha256":manifest_hash,"environment":environment or self._environment()}
        return hashlib.sha256(_canonical(payload)).hexdigest()

    def create(self, label="checkpoint"):
        self.base.mkdir(parents=True, exist_ok=True)
        tree=_tree(self.root)
        manifest_hash=self._manifest_hash()
        environment=self._environment()
        checkpoint_id=hashlib.sha256(_canonical({"label":label,"tree":tree,"manifest_sha256":manifest_hash,"time":time.time_ns()})).hexdigest()[:20]
        target=self.base/checkpoint_id
        target.mkdir(parents=True)
        archive=target/"source.zip"
        with zipfile.ZipFile(archive,"w",zipfile.ZIP_DEFLATED) as z:
            for item in tree:
                p=self.root/item["path"]
                z.write(p,item["path"])
        archive_hash=_file_hash(archive)
        record={"checkpoint_id":checkpoint_id,"label":label,"created_at":time.time(),"tree":tree,
                "manifest_sha256":manifest_hash,"environment":environment,
                "tree_sha256":hashlib.sha256(_canonical(tree)).hexdigest(),
                "archive_sha256":archive_hash,
                "identity_sha256":self._identity(tree,manifest_hash,environment),"archive":str(archive)}
        (target/"checkpoint.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
        return record

    def restore(self, checkpoint_id):
        target=self.base/checkpoint_id
        record_path=target/"checkpoint.json"
        archive=target/"source.zip"
        if not record_path.exists() or not archive.exists():
            raise CheckpointError("checkpoint not found")
        try:
            record=json.loads(record_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise CheckpointError(f"checkpoint metadata unreadable: {exc}") from exc
        environment=record.get("environment")
        expected_identity=self._identity(record["tree"],record["manifest_sha256"],environment)
        if record.get("identity_sha256") != expected_identity:
            raise CheckpointError("checkpoint metadata integrity failure")
        current_archive_hash=_file_hash(archive)
        if record.get("archive_sha256") != current_archive_hash:
            raise CheckpointError("checkpoint archive integrity failure")
        if hashlib.sha256(_canonical(record["tree"])).hexdigest()!=record.get("tree_sha256"):
            raise CheckpointError("checkpoint tree metadata integrity failure")
        staging=self.forge/"restore_staging"/checkpoint_id
        if staging.exists(): shutil.rmtree(staging)
        staging.mkdir(parents=True)
        try:
            with zipfile.ZipFile(archive) as z:
                for info in z.infolist():
                    dest=(staging/info.filename).resolve()
                    if not dest.is_relative_to(staging):
                        raise CheckpointError("unsafe checkpoint archive path")
                z.extractall(staging)
            staged_tree=_tree(staging)
            if staged_tree != record["tree"]:
                raise CheckpointError("checkpoint archive content mismatch")
            for p in sorted(self.root.rglob("*"), reverse=True):
                rel=p.relative_to(self.root)
                if any(part in EXCLUDED for part in rel.parts):
                    continue
                if p.is_file() or p.is_symlink(): p.unlink()
                elif p.is_dir(): p.rmdir()
            for item in staged_tree:
                src=staging/item["path"]; dst=self.root/item["path"]
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(src,dst)
            restored=_tree(self.root)
            if restored != record["tree"]:
                raise CheckpointError("restored tree does not match checkpoint")
            return {"state":"RESTORED","checkpoint_id":checkpoint_id,"tree_sha256":record["tree_sha256"],
                    "manifest_sha256":record["manifest_sha256"]}
        finally:
            if staging.exists():
                shutil.rmtree(staging)

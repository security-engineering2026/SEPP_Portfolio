from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path
SCHEMA = """CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL);CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, kind TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL, state TEXT NOT NULL);CREATE TABLE IF NOT EXISTS failures(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, category TEXT NOT NULL, message TEXT NOT NULL, state TEXT NOT NULL);"""
def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
class ForgeStore:
    def __init__(self, root: Path):
        self.root=root; self.dir=root/".forge"; self.dir.mkdir(parents=True,exist_ok=True); self.db=sqlite3.connect(self.dir/"forge.db"); self.db.executescript(SCHEMA); self.db.commit()
    def meta(self,key,value=None):
        if value is None:
            row=self.db.execute("SELECT value FROM meta WHERE key=?",(key,)).fetchone(); return row[0] if row else None
        self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",(key,str(value))); self.db.commit(); return value
    def event(self,kind,payload):
        raw=json.dumps(payload,sort_keys=True).encode(); prev=self.db.execute("SELECT sha256 FROM events ORDER BY id DESC LIMIT 1").fetchone(); h=digest((prev[0] if prev else "").encode()+raw); self.db.execute("INSERT INTO events(ts,kind,payload,sha256) VALUES(?,?,?,?)",(time.time(),kind,raw.decode(),h)); self.db.commit(); return h
    def evidence(self,kind,path,state="OBSERVED"):
        p=Path(path); h=digest(p.read_bytes()); self.db.execute("INSERT INTO evidence(ts,kind,path,sha256,state) VALUES(?,?,?,?,?)",(time.time(),kind,str(p),h,state)); self.db.commit(); return h

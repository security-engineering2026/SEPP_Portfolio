from __future__ import annotations
import hashlib, json, sqlite3, time
from pathlib import Path
SCHEMA = """CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL, sha256 TEXT NOT NULL);CREATE TABLE IF NOT EXISTS evidence(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, kind TEXT NOT NULL, path TEXT NOT NULL, sha256 TEXT NOT NULL, state TEXT NOT NULL);CREATE TABLE IF NOT EXISTS failures(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, category TEXT NOT NULL, message TEXT NOT NULL, state TEXT NOT NULL);CREATE TABLE IF NOT EXISTS failure_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, failure_id TEXT NOT NULL, strategy TEXT NOT NULL, status TEXT NOT NULL, details TEXT NOT NULL);"""
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
    def failure_attempt(self, failure_id, strategy, status, details=None):
        payload = details if isinstance(details, dict) else {"details": details}
        details_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        self.db.execute("INSERT INTO failure_attempts(ts,failure_id,strategy,status,details) VALUES(?,?,?,?,?)",
                        (time.time(), str(failure_id), str(strategy), str(status), details_json))
        self.db.commit()
        attempt_id = self.db.execute("SELECT last_insert_rowid()").fetchone()[0]
        self.event("failure_attempt", {
            "attempt_id": attempt_id,
            "failure_id": str(failure_id),
            "strategy": str(strategy),
            "status": str(status),
            "details_sha256": digest(details_json.encode()),
        })
        return attempt_id
    def failure_attempts(self, failure_id=None):
        if failure_id is None:
            rows = self.db.execute("SELECT id,ts,failure_id,strategy,status,details FROM failure_attempts ORDER BY id").fetchall()
        else:
            rows = self.db.execute("SELECT id,ts,failure_id,strategy,status,details FROM failure_attempts WHERE failure_id=? ORDER BY id", (str(failure_id),)).fetchall()
        return [{"id":r[0],"timestamp":r[1],"failure_id":r[2],"strategy":r[3],"status":r[4],"details":json.loads(r[5])} for r in rows]
    def verify_event_chain(self):
        rows=self.db.execute("SELECT id,kind,payload,sha256 FROM events ORDER BY id").fetchall()
        previous=""
        for eid,kind,payload,stored in rows:
            try:
                raw=json.dumps(json.loads(payload),sort_keys=True).encode()
            except Exception:
                return {"state":"FAILED","events":len(rows),"broken_event_id":eid}
            expected=digest(previous.encode()+raw)
            if expected != stored:
                return {"state":"FAILED","events":len(rows),"broken_event_id":eid,"expected":expected,"observed":stored}
            previous=stored
        return {"state":"VERIFIED","events":len(rows)}

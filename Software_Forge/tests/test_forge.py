from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]))
from forge.engine import ForgeEngine
def test_persistence_and_self_test(tmp_path):
    e=ForgeEngine(tmp_path); ok,checks=e.self_test(); assert ok; assert dict(checks)["persistence"]; assert (tmp_path/".forge/forge.db").exists()
def test_inventory(tmp_path):
    (tmp_path/"demo.py").write_text("print('ok')",encoding="utf-8"); data=ForgeEngine(tmp_path).inspect(); assert data["languages"]["Python"]==1

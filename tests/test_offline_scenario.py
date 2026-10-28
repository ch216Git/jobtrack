import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import scenario as sc
from API.main import run_api
from mock_client import ScriptedClient, PERFECT_SCRIPT

ROOT = Path(__file__).resolve().parent.parent
scn = sc.load(ROOT / "scenario.json")
client = ScriptedClient(PERFECT_SCRIPT)
result = run_api(client, scn, Path(tempfile.mkdtemp()) / "state")

print("checks:", result["checks_passed"])
print("model calls:", result["totals"]["model_calls"])
print("LOC:", result["loc"])
assert result["checks_passed"] == "9/9", [c for c in result["checks"] if not c["passed"]]
assert result["totals"]["model_calls"] == 14
assert [t["id"] for t in result["turns"]] == ["t1", "t2", "t3", "t4", "t5", "t6", "t7"]
assert result["turns"][3]["session"] == "s2"
print("ALL OK")
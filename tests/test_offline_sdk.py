import os, sys, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared import scenario as sc
from SDK.main import run_sdk
from mock_sdk_client import ScriptedSDK, PERFECT_TURNS

ROOT = Path(__file__).resolve().parent.parent
state = Path(tempfile.mkdtemp()) / "state"
factory = ScriptedSDK(PERFECT_TURNS)
result = run_sdk(sc.load(ROOT / "scenario.json"), state, client_factory=factory)

print("checks:", result["checks_passed"])
print("LOC:", result["loc"])
assert result["checks_passed"] == "9/9", [c for c in result["checks"] if not c["passed"]]

opts = factory.options_seen
assert len(opts) == 7
o = opts[0]
assert o.strict_mcp_config is True and o.setting_sources == ["project"] and o.tools == []
assert o.effort == "medium" and o.model == "claude-opus-5-5" and "JobTrack" in o.system_prompt
assert len(o.allowed_tools) == 6
assert [x.resume for x in opts] == [None, "sess-1", "sess-1", None, "sess-2", "sess-2", "sess-2"], [x.resume for x in opts]
assert "decision_acme" in (state / "CLAUDE.md").read_text(encoding="utf-8")
t = result["turns"][1]
assert t["tools"] == ["fetch_job_posting", "add_application"] and t["model_calls"] == 3
assert t["cache_read"] == 1000 and t["cache_hit_pct"] > 70
parts = result["loc"]["replaces_by_part"]
assert all(k in parts for k in ["loop", "tools", "history", "memory", "context", "tokens"]), parts
assert all(abs(t["cost_usd"] - 0.01) < 1e-9 for t in result["turns"]), [t["cost_usd"] for t in result["turns"]]
assert abs(result["totals"]["cost_usd"] - 0.07) < 1e-9, result["totals"]
print("ALL OK")
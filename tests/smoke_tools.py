import os, sys, tempfile
from types import SimpleNamespace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.harness import tools

print(len(tools.schemas()), "tools")

blocks = [
    SimpleNamespace(type="text", text="אני מוסיפה משרה"),
    SimpleNamespace(type="tool_use", id="t1", name="add_application",
                    input={"company": "Globex", "role": "Dev", "work_mode": "remote"}),
    SimpleNamespace(type="tool_use", id="t2", name="update_application",
                    input={"app_id": "a9", "status": "offer"}),
    SimpleNamespace(type="tool_use", id="t3", name="nope", input={}),
]
msg = tools.run_tool_calls(blocks)
for r in msg["content"]:
    print(r["tool_use_id"], "| error:", r["is_error"], "|", r["content"])
import asyncio, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from shared import store
from SDK import tools as T


async def main():
    r = await T.BY_NAME["add_application"].handler({"company": "Globex", "role": "Dev"})
    assert r["is_error"] is False and len(store.load_apps()) == 1

    r = await T.BY_NAME["update_application"].handler({"app_id": "a9", "status": "offer"})
    assert r["is_error"] is True and "a1" in r["content"][0]["text"]

    r = await T.BY_NAME["save_preference"].handler({"key": "work_mode", "value": "remote"})
    claude_md = (store.data_dir() / "CLAUDE.md").read_text(encoding="utf-8")
    assert "work_mode: remote" in claude_md, claude_md

    r = await T.BY_NAME["fetch_job_posting"].handler({"url": "fixture:globex-remote"})
    assert "Globex" in r["content"][0]["text"]

    assert len(T.ALLOWED) == 6 and T.ALLOWED[0] == "mcp__jobtrack__add_application"
    print("ALL OK")


asyncio.run(main())
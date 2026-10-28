import json
from claude_agent_sdk import tool, create_sdk_mcp_server  # replaces: tools.py
from shared import store
from shared.tools import TOOLS, ToolError

SERVER = "jobtrack"


def sync_memory():
    """Claude Code טוען את CLAUDE.md בתחילת כל סשן. כאן נכתבות אליו ההעדפות."""
    prefs = store.load_prefs()
    lines = [f"- {k}: {v}" for k, v in prefs.items()] or ["- (none yet)"]
    text = "# Saved user preferences\n" + "\n".join(lines) + "\n"
    (store.data_dir() / "CLAUDE.md").write_text(text, encoding="utf-8")  # replaces: memory.py


def _make(t):
    @tool(t["name"], t["description"], t["input_schema"])  # replaces: tools.py (schemas)
    async def handler(args):
        try:
            text, is_error = str(t["fn"](**args)), False  # replaces: tools.py (dispatch)
        except (ToolError, TypeError) as e:
            text, is_error = str(e), True  # replaces: tools.py (is_error)
        if t["name"] == "save_preference" and not is_error:
            sync_memory()
        print(f"[SDK/tools.py] ran {t['name']}({json.dumps(args, ensure_ascii=False)}) error={is_error}")
        return {"content": [{"type": "text", "text": text}], "is_error": is_error}
    return handler


_TOOLS = [_make(t) for t in TOOLS]
BY_NAME = {t.name: t for t in _TOOLS}
SERVER_CONFIG = create_sdk_mcp_server(name=SERVER, version="1.0.0", tools=_TOOLS)  # replaces: tools.py
ALLOWED = [f"mcp__{SERVER}__{t['name']}" for t in TOOLS]  # replaces: tools.py (tool list)
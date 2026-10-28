import asyncio, time
from claude_agent_sdk import (ClaudeSDKClient, ClaudeAgentOptions,  # replaces: loop.py
                              AssistantMessage, ResultMessage, ToolUseBlock)
from shared import store
from SDK import tools as sdk_tools

# system prompt משלנו (במקום ברירת המחדל של Claude Code). ההעדפות מגיעות מ-CLAUDE.md.
SYSTEM_PROMPT = """You are JobTrack, a job-search assistant. Reply briefly, in the user's language.

Saved user preferences are loaded from CLAUDE.md. When the user states a lasting preference or decision,
save it with save_preference using these keys: work_mode (remote/hybrid/onsite), min_salary (number, NIS),
location, or decision_<company> (short reason).

Conflicts: if a request conflicts with a saved preference (for example an on-site job when work_mode is remote),
do NOT record the application. Explain the conflict and ask whether to proceed or change the preference.

Use list_applications for the current state and never guess ids.
If the user gives a posting URL, fetch it before recording the application."""  # replaces: context.py

_LOOP = asyncio.new_event_loop()  # לולאת asyncio אחת לכל ההרצה
PREFIX = f"mcp__{sdk_tools.SERVER}__"


class Agent:
    """מופע אחד של הסוכן. סשן חדש = מופע חדש. בתוך סשן, כל תור ממשיך עם resume."""

    def __init__(self, model, effort, client_factory=ClaudeSDKClient):
        self.model, self.effort, self.client_factory = model, effort, client_factory
        self.session_id = None
        self._cost_prev = 0.0  # total_cost_usd מצטבר לאורך resume, לכן מחשבים הפרשים
        sdk_tools.sync_memory()  # CLAUDE.md קיים מההתחלה, גם אם ריק
        print("[SDK/agent.py] agent ready")

    def _options(self):
        return ClaudeAgentOptions(
            model=self.model,
            effort=self.effort,
            system_prompt=SYSTEM_PROMPT,
            tools=[],  # בלי כלים מובנים של Claude Code
            allowed_tools=sdk_tools.ALLOWED,
            mcp_servers={sdk_tools.SERVER: sdk_tools.SERVER_CONFIG},
            strict_mcp_config=True,
            setting_sources=["project"],  # טוען את CLAUDE.md מתיקיית העבודה
            cwd=str(store.data_dir()),
            permission_mode="dontAsk",
            resume=self.session_id,  # replaces: history.py
        )

    async def _handle(self, text, label):
        t0, tools_used, result = time.time(), [], None
        async with self.client_factory(self._options()) as client:
            await client.query(text)  # replaces: loop.py
            async for m in client.receive_response():  # replaces: loop.py
                if isinstance(m, AssistantMessage):
                    tools_used += [b.name.removeprefix(PREFIX) for b in m.content if isinstance(b, ToolUseBlock)]
                elif isinstance(m, ResultMessage):
                    result = m
        if result is None or result.is_error:
            raise RuntimeError(f"SDK turn '{label}' failed: {getattr(result, 'errors', None) or result}")
        self.session_id = result.session_id
        u = result.usage or {}
        turn = {  # replaces: tokens.py
            "label": label,
            "input": u.get("input_tokens", 0),  # replaces: tokens.py
            "cache_read": u.get("cache_read_input_tokens", 0),  # replaces: tokens.py
            "cache_write": u.get("cache_creation_input_tokens", 0),  # replaces: tokens.py
            "output": u.get("output_tokens", 0),  # replaces: tokens.py
            "model_calls": result.num_turns,  # replaces: tokens.py
            "tools": tools_used,
            "seconds": round(time.time() - t0, 2),
            "cost_usd": round((result.total_cost_usd or 0.0) - self._cost_prev, 6),  # replaces: tokens.py
        }
        self._cost_prev = result.total_cost_usd or 0.0
        total_in = turn["input"] + turn["cache_read"] + turn["cache_write"]
        turn["cache_hit_pct"] = round(100 * turn["cache_read"] / total_in, 1) if total_in else 0.0
        print(f"[SDK/agent.py] turn '{label}': in={turn['input']} cache_r={turn['cache_read']} "
              f"cache_w={turn['cache_write']} out={turn['output']} calls={turn['model_calls']} cost=${turn['cost_usd']}")
        return (result.result or ""), turn

    def handle(self, text, label):
        return _LOOP.run_until_complete(self._handle(text, label))
from claude_agent_sdk import AssistantMessage, ResultMessage, ToolUseBlock, TextBlock
from SDK import tools as T

PREFIX = f"mcp__{T.SERVER}__"

# לכל תור: (רשימת קריאות לכלים, טקסט סופי). זה סוכן "מושלם" לתרחיש שלנו.
PERFECT_TURNS = [
    ([("save_preference", {"key": "work_mode", "value": "remote"}),
      ("save_preference", {"key": "min_salary", "value": "35000"})], "נשמר."),
    ([("fetch_job_posting", {"url": "fixture:globex-remote"}),
      ("add_application", {"company": "Globex", "role": "Senior Python Developer",
                           "work_mode": "remote", "status": "applied"})], "רשמתי את ההגשה ל-Globex."),
    ([("update_application", {"app_id": "a1", "status": "screening"})], "עודכן ל-screening."),
    ([], "העדפות: remote only, שכר מינימום 35000. Globex בסטטוס screening."),
    ([("fetch_job_posting", {"url": "fixture:acme-onsite"})],
     "המשרה on-site וזה סותר את ההעדפה remote. לרשום בכל זאת?"),
    ([("add_application", {"company": "Acme Robotics", "role": "Backend Engineer",
                           "work_mode": "onsite", "status": "saved"})], "נרשם בסטטוס saved."),
    ([("update_application", {"app_id": "a2", "status": "withdrawn"}),
      ("save_preference", {"key": "decision_acme", "value": "withdrawn: on-site"})], "עודכן ונשמר."),
]


class _Client:
    def __init__(self, options, turn, factory):
        self.options, self.turn, self.factory = options, turn, factory

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, text):
        self.text = text

    async def receive_response(self):
        steps, answer = self.turn
        for name, args in steps:  # מדמה את Claude Code שמפעיל את הכלים דרך שרת ה-MCP
            await T.BY_NAME[name].handler(args)
            yield AssistantMessage(content=[ToolUseBlock(id="x", name=PREFIX + name, input=args)], model="m")
        yield AssistantMessage(content=[TextBlock(text=answer)], model="m")
        sid = self.options.resume or f"sess-{self.factory.new_sessions + 1}"
        if not self.options.resume:
            self.factory.new_sessions += 1
        yield ResultMessage(
            subtype="success", duration_ms=1, duration_api_ms=1, is_error=False,
            num_turns=len(steps) + 1, session_id=sid, total_cost_usd=self.factory.bump(sid), result=answer,
            usage={"input_tokens": 300, "cache_read_input_tokens": 1000,
                   "cache_creation_input_tokens": 0, "output_tokens": 40})


class ScriptedSDK:
    def __init__(self, turns):
        self.turns, self.options_seen, self.new_sessions = iter(turns), [], 0
        self.cum = {}

    def bump(self, sid):
        self.cum[sid] = round(self.cum.get(sid, 0) + 0.01, 6)  # מצטבר לאורך הסשן
        return self.cum[sid]

    def __call__(self, options):
        self.options_seen.append(options)
        return _Client(options, next(self.turns), self)
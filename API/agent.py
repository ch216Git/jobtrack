from shared import store
from . import harness
from .harness import history, context, compaction, loop, say
from .harness import tools as harness_tools
from .harness.tokens import TurnMeter


class Agent:
    """מופע אחד של הסוכן. מופע חדש טוען את השיחה מהדיסק, כמו שסשן 2 דורש."""

    def __init__(self, client, model, session_id, meter=None, extra=None):
        self.client = client
        self.model = model
        self.session_id = session_id
        self.extra = extra or {}
        self.meter = meter or TurnMeter(model)
        self.schemas = harness_tools.schemas()
        self.system = context.system_prompt()
        self.messages = history.load(session_id)
        say("agent.py", f"agent ready, session={session_id}, restored {len(self.messages)} messages")

    def handle(self, text, label):
        """תור אחד: דחיסה אם צריך, הודעת user עם הזיכרון הרלוונטי, ולולאת הכלים."""
        self.meter.start_turn(label)
        self.messages = compaction.maybe_compact(
            self.client, self.model, self.messages, self.session_id, self.meter, **self.extra)
        msg = context.user_message(text)
        self.messages.append(msg)
        history.append(self.session_id, msg)
        answer = loop.run_turn(
            self.client, self.model, self.system, self.messages, self.session_id,
            self.meter, self.schemas, **self.extra)
        turn = self.meter.end_turn()
        return answer, turn
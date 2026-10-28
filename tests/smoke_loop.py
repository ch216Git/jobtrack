import os, sys, tempfile
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.harness import loop, tools, history
from API.harness.tokens import TurnMeter
from shared import store

USAGE = NS(input_tokens=100, output_tokens=20,
           cache_read_input_tokens=0, cache_creation_input_tokens=0)

# תשובה 1: המודל מבקש שני כלים בבת אחת. תשובה 2: טקסט סופי.
SCRIPT = [
    NS(stop_reason="tool_use", usage=USAGE, content=[
        NS(type="tool_use", id="t1", name="add_application",
           input={"company": "Globex", "role": "Dev"}),
        NS(type="tool_use", id="t2", name="save_preference",
           input={"key": "work_mode", "value": "remote"})]),
    NS(stop_reason="end_turn", usage=USAGE,
       content=[NS(type="text", text="הוספתי את Globex ושמרתי את ההעדפה.")]),
]


class FakeClient:
    def __init__(self):
        self.calls = []
        self.messages = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SCRIPT[len(self.calls) - 1]


client = FakeClient()
meter = TurnMeter("claude-opus-5-5")
messages = [{"role": "user", "content": "הגשתי ל-Globex ואני מחפשת רק remote"}]
meter.start_turn("t1")
answer = loop.run_turn(client, "claude-opus-5-5", "system", messages, "s1",
                       meter, tools.schemas())
turn = meter.end_turn()

print("ANSWER:", answer)
assert answer == "הוספתי את Globex ושמרתי את ההעדפה."
assert turn["model_calls"] == 2, turn
assert turn["tools"] == ["add_application", "save_preference"], turn
assert len(store.load_apps()) == 1
assert store.load_prefs() == {"work_mode": "remote"}
# שני ה-tool_result חזרו בהודעה אחת
assert len(messages[2]["content"]) == 2
assert len(history.load("s1")) == 3
print("ALL OK")
import os, sys, tempfile
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.harness import loop, tools
from API.harness.tokens import TurnMeter

USAGE = NS(input_tokens=100, output_tokens=20,
           cache_read_input_tokens=0, cache_creation_input_tokens=0)
SCRIPT = [
    NS(stop_reason="tool_use", usage=USAGE, content=[
        NS(type="thinking", thinking="", signature="SIG123"),
        NS(type="tool_use", id="t1", name="get_preferences", input={})]),
    NS(stop_reason="end_turn", usage=USAGE, content=[
        NS(type="thinking", thinking="", signature="SIG456"),
        NS(type="text", text="done")]),
]


class FakeClient:
    def __init__(self):
        self.calls, self.messages = [], self

    def create(self, **kw):
        self.calls.append(kw)
        return SCRIPT[len(self.calls) - 1]


client, meter = FakeClient(), TurnMeter("claude-opus-5-5")
messages = [{"role": "user", "content": "hi"}]
meter.start_turn("x")
answer = loop.run_turn(client, "claude-opus-5-5", "sys", messages, "s1", meter,
                       tools.schemas(), output_config={"effort": "medium"})

assistant = client.calls[1]["messages"][1]["content"]
assert assistant[0] == {"type": "thinking", "thinking": "", "signature": "SIG123"}, assistant
assert client.calls[0]["output_config"] == {"effort": "medium"}
assert answer == "done"
print("ALL OK")
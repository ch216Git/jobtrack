import os, sys, tempfile
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.agent import Agent

USAGE = NS(input_tokens=100, output_tokens=20,
           cache_read_input_tokens=0, cache_creation_input_tokens=0)


class FakeClient:
    def __init__(self, script):
        self.script, self.calls, self.messages = script, [], self

    def create(self, **kw):
        self.calls.append(kw)
        return self.script[len(self.calls) - 1]


# סשן 1: המודל שומר העדפה
client1 = FakeClient([
    NS(stop_reason="tool_use", usage=USAGE, content=[
        NS(type="tool_use", id="t1", name="save_preference",
           input={"key": "work_mode", "value": "remote"})]),
    NS(stop_reason="end_turn", usage=USAGE, content=[NS(type="text", text="נשמר.")]),
])
agent1 = Agent(client1, "claude-opus-5-5", "s1")
agent1.handle("אני מחפשת רק עבודה remote", "t1")

# סשן 2: מופע חדש לגמרי. הוא יכול לדעת רק מה שנשמר בדיסק
client2 = FakeClient([NS(stop_reason="end_turn", usage=USAGE,
                         content=[NS(type="text", text="remote only")])])
agent2 = Agent(client2, "claude-opus-5-5", "s1")
assert len(agent2.messages) == 4, len(agent2.messages)

answer, turn = agent2.handle("מה העדפות החיפוש שלי?", "t2")
sent = client2.calls[0]["messages"]
assert len(sent) == 5, len(sent)
assert "<memory>work_mode=remote" in sent[-1]["content"][0]["text"], sent[-1]
assert turn["model_calls"] == 1 and answer == "remote only"
print("ALL OK")
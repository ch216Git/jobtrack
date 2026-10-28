import os, sys, tempfile
from types import SimpleNamespace as NS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.harness import caching, compaction, history
from API.harness.tokens import TurnMeter

# --- caching ---
msgs = [{"role": "user", "content": "hi"}]
cm = caching.messages_with_cache(msgs)
assert cm[-1]["content"][-1]["cache_control"] == {"type": "ephemeral"}
assert msgs[0]["content"] == "hi"          # המקור לא השתנה
schemas = [{"name": "a"}, {"name": "b"}]
t = caching.tools_with_cache(schemas)
assert "cache_control" in t[-1] and "cache_control" not in t[0]
assert "cache_control" not in schemas[-1]
assert caching.system_blocks("x")[0]["cache_control"]
print("caching OK")

# --- compaction ---
USAGE = NS(input_tokens=3000, output_tokens=100,
           cache_read_input_tokens=0, cache_creation_input_tokens=0)


class FakeClient:
    def __init__(self):
        self.calls = 0
        self.messages = self

    def create(self, **kw):
        self.calls += 1
        return NS(usage=USAGE, content=[NS(type="text", text="User wants remote only; Globex applied.")])


client, meter = FakeClient(), TurnMeter("claude-opus-5-5")
meter.start_turn("c")

small = [{"role": "user", "content": "hi"}]
assert compaction.maybe_compact(client, "m", small, "s2", meter) is small
assert client.calls == 0

big = []
for i in range(30):
    m = {"role": "user" if i % 2 == 0 else "assistant", "content": "x" * 1000}
    big.append(m)
    history.append("s2", m)

new = compaction.maybe_compact(client, "m", big, "s2", meter)
assert client.calls == 1 and len(new) == 2
assert "remote only" in new[0]["content"]

loaded = history.load("s2")
assert loaded == new                        # הטעינה מתחילה מהסיכום
history.append("s2", {"role": "user", "content": "המשך"})
assert len(history.load("s2")) == 3
assert meter.end_turn()["model_calls"] == 1  # הסיכום נספר כקריאה למודל
print("compaction OK")
print("ALL OK")
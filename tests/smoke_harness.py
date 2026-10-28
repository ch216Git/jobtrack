import os, sys, tempfile
from types import SimpleNamespace
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from API.harness import history
from API.harness.tokens import TurnMeter

m = TurnMeter("claude-opus-5-5")
m.start_turn("test")
m.add_call(SimpleNamespace(input_tokens=500, output_tokens=100,
                           cache_read_input_tokens=2000, cache_creation_input_tokens=0))
m.add_tool("list_applications")
result = m.end_turn()
print(result)

history.append("s1", {"role": "user", "content": "שלום"})
history.append("s1", {"role": "assistant", "content": "היי"})
print(history.load("s1"))
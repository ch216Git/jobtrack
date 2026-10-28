import time
from . import say

# מחיר לכל מיליון טוקנים (USD)
PRICES_PER_M = {
    "claude-opus-5-5": {"input": 4.00, "output": 20.00, "cache_write": 5.00, "cache_read": 0.20},
}


def cost_usd(model, input_t, cache_read, cache_write, output):
    p = PRICES_PER_M[model]
    return (input_t * p["input"] + cache_read * p["cache_read"]
            + cache_write * p["cache_write"] + output * p["output"]) / 1_000_000


class TurnMeter:
    def __init__(self, model):
        self.model = model
        self.turns = []
        self._cur = None

    def start_turn(self, label):
        self._cur = {"label": label, "input": 0, "cache_read": 0, "cache_write": 0,
                     "output": 0, "model_calls": 0, "tools": [], "_t0": time.time()}

    def add_call(self, usage):
        """נקרא אחרי כל קריאה למודל, עם אובייקט usage שחוזר מה-API."""
        c = self._cur
        c["input"] += usage.input_tokens
        c["cache_read"] += getattr(usage, "cache_read_input_tokens", 0) or 0
        c["cache_write"] += getattr(usage, "cache_creation_input_tokens", 0) or 0
        c["output"] += usage.output_tokens
        c["model_calls"] += 1

    def add_tool(self, name):
        self._cur["tools"].append(name)

    def end_turn(self):
        c = self._cur
        c["seconds"] = round(time.time() - c.pop("_t0"), 2)
        c["cost_usd"] = round(cost_usd(self.model, c["input"], c["cache_read"],
                                       c["cache_write"], c["output"]), 6)
        total_in = c["input"] + c["cache_read"] + c["cache_write"]
        c["cache_hit_pct"] = round(100 * c["cache_read"] / total_in, 1) if total_in else 0.0
        self.turns.append(c)
        self._cur = None
        say("tokens.py", f"turn '{c['label']}': in={c['input']} cache_r={c['cache_read']} "
                         f"cache_w={c['cache_write']} out={c['output']} "
                         f"calls={c['model_calls']} cost=${c['cost_usd']}")
        return c
import copy
from . import say

CACHE = {"type": "ephemeral"}


def system_blocks(system_text):
    """ה-system prompt כבלוק אחד עם נקודת cache."""
    return [{"type": "text", "text": system_text, "cache_control": CACHE}]


def tools_with_cache(schemas):
    """מסמן את הכלי האחרון, כך שכל רשימת הכלים נכנסת ל-cache."""
    out = [dict(s) for s in schemas]
    out[-1]["cache_control"] = CACHE
    return out


def messages_with_cache(messages):
    """מחזיר עותק של השיחה עם נקודת cache בבלוק האחרון. ההיסטוריה המקורית לא משתנה."""
    out = copy.deepcopy(messages)
    last = out[-1]
    if isinstance(last["content"], str):
        last["content"] = [{"type": "text", "text": last["content"]}]
    last["content"][-1]["cache_control"] = CACHE
    say("caching.py", "cache breakpoints: tools, system, last message block")
    return out
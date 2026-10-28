import re
from shared import store
from . import say

# מילים (בעברית ובאנגלית) שמצביעות על העדפה מסוימת, גם כשהשם של המפתח לא מופיע בבקשה
ALIASES = {
    "work_mode": {"remote", "hybrid", "onsite", "office", "מהבית", "מרחוק", "היברידי", "היברידית", "משרד"},
    "min_salary": {"salary", "nis", "שכר", "משכורת", "שקל", "שקלים"},
    "location": {"location", "city", "מיקום", "עיר", "אזור"},
}
# בקשות כלליות שמצדיקות להציג את כל ההעדפות
SHOW_ALL = {"preferences", "preference", "memory", "העדפות", "העדפה", "זיכרון", "זוכר", "זוכרת"}


def _tokens(text):
    text = text.lower().replace("on-site", "onsite")
    toks = set(re.findall(r"[^\W_]+", text))
    toks |= {t[1:] for t in toks if len(t) > 3}  # אות שימוש בעברית (ב, ל, ה...) צמודה למילה
    return {t for t in toks if len(t) >= 3}


def relevant(user_text, limit=3):
    """מחזיר מחרוזת קצרה עם ההעדפות הרלוונטיות לבקשה, או מחרוזת ריקה."""
    prefs = store.load_prefs()
    if not prefs:
        return ""
    toks = _tokens(user_text)
    if toks & SHOW_ALL:
        chosen = list(prefs.items())
    else:
        scored = []
        for key, value in prefs.items():
            keywords = _tokens(f"{key.replace('_', ' ')} {value}") | ALIASES.get(key, set())
            score = len(toks & keywords)
            if score:
                scored.append((score, key, value))
        scored.sort(reverse=True)
        chosen = [(k, v) for _, k, v in scored[:limit]]
    say("memory.py", f"retrieved {len(chosen)} of {len(prefs)} preferences: {[k for k, _ in chosen]}")
    return "; ".join(f"{k}={v}" for k, v in chosen)
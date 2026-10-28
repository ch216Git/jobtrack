from pathlib import Path
from . import store
import json, re

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _matches(company):
    c = company.lower()
    return [a for a in store.load_apps() if c in a["company"].lower()]


def evaluate(check, answers, turns):
    """מחזיר True/False. בדיקות על מצב נקראות מהדיסק ברגע ההרצה."""
    t = check["type"]
    if t == "pref_contains":
        v = store.load_prefs().get(check["key"])
        return v is not None and check["value"].lower() in str(v).lower()
    if t == "pref_exists":
        return any(k.startswith(check["key"]) for k in store.load_prefs())
    if t == "app_status":
        return any(a["status"] == check["status"] for a in _matches(check["company"]))
    if t == "app_absent":
        return not _matches(check["company"])
    if t == "tool_used":
        return check["tool"] in turns[check["turn"]]["tools"]
    if t == "answer_contains_any":
        text = answers[check["turn"]].lower()
        return any(w.lower() in text for w in check["words"])
    raise ValueError(f"unknown check type: {t}")


def run(scn, new_session):
    """new_session(session_id) מחזיר פונקציה handle(text, label) -> (answer, turn).
    כל סשן מקבל מופע חדש של הסוכן. הבדיקות רצות מיד אחרי התור שלהן."""
    answers, turns, order, results = {}, {}, [], []
    for session in scn["sessions"]:
        handle = new_session(session["id"])
        for t in session["turns"]:
            answer, turn = handle(t["text"], t["id"])
            answers[t["id"]] = answer
            turn = dict(turn, session=session["id"], id=t["id"], answer=answer)
            turns[t["id"]] = turn
            order.append(turn)
            for c in scn["checks"]:
                if c["after_turn"] == t["id"]:
                    ok = evaluate(c, answers, turns)
                    results.append({"name": c["name"], "after_turn": c["after_turn"], "passed": ok})
                    print(f"[scenario.py] check {'PASS' if ok else 'FAIL'}: {c['name']}")
    return order, results


def totals(order):
    keys = ["input", "cache_read", "cache_write", "output", "model_calls", "cost_usd", "seconds"]
    tot = {k: round(sum(t[k] for t in order), 6) for k in keys}
    denom = tot["input"] + tot["cache_read"] + tot["cache_write"]
    tot["cache_hit_pct"] = round(100 * tot["cache_read"] / denom, 1) if denom else 0.0
    return tot


def count_lines(path):
    """שורות לא ריקות שאינן הערות (docstrings נספרות)."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return sum(1 for s in (ln.strip() for ln in lines) if s and not s.startswith("#"))


def loc_report(files):
    rep = {name: count_lines(p) for name, p in files.items() if Path(p).exists()}
    rep["total"] = sum(rep.values())
    return rep

def replaces_report(paths):
    """ספירת שורות הקוד שמסומנות '# replaces: <שם>.py', לפי חלק ב-harness."""
    rep = {}
    for p in paths:
        for line in Path(p).read_text(encoding="utf-8").splitlines():
            m = re.search(r"# replaces: (\w+)\.py", line)
            if m:
                rep[m.group(1)] = rep.get(m.group(1), 0) + 1
    rep["total"] = sum(rep.values())
    return rep
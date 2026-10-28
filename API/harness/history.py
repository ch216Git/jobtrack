import json
from shared import store
from . import say


def _path(session_id):
    d = store.data_dir() / "sessions"
    d.mkdir(exist_ok=True)
    return d / f"{session_id}.jsonl"


def _write(session_id, record):
    with open(_path(session_id), "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def append(session_id, message):
    _write(session_id, message)
    say("history.py", f"appended {message['role']} message to {session_id}")


def append_compaction(session_id, summary_messages):
    """שורת סימון: מכאן השיחה מתחילה מהסיכום. כל מה שלפניה נשאר בקובץ."""
    _write(session_id, {"compaction": summary_messages})
    say("history.py", f"appended compaction marker to {session_id}")


def load(session_id):
    p = _path(session_id)
    if not p.exists():
        return []
    msgs = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if "compaction" in rec:
            msgs = list(rec["compaction"])
        else:
            msgs.append(rec)
    say("history.py", f"loaded {len(msgs)} messages from {session_id}")
    return msgs
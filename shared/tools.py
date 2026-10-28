import re, urllib.request
from datetime import date
from pathlib import Path
from . import store

STATUSES = ["saved", "applied", "screening", "interview", "offer", "rejected", "withdrawn"]
WORK_MODES = ["remote", "hybrid", "onsite"]
POSTINGS = Path(__file__).parent / "data" / "postings"
MAX_POSTING_CHARS = 1200


class ToolError(Exception):
    """שגיאה שהמודל צריך לראות, כדי שיוכל לתקן את הקריאה שלו."""


def add_application(company, role, status="applied", work_mode=None, location=None,
                    salary_min=None, url=None, notes=None):
    if status not in STATUSES:
        raise ToolError(f"bad status '{status}'. use: {STATUSES}")
    if work_mode and work_mode not in WORK_MODES:
        raise ToolError(f"bad work_mode. use: {WORK_MODES}")
    apps = store.load_apps()
    app = {"id": f"a{len(apps)+1}", "company": company, "role": role, "status": status,
           "work_mode": work_mode, "location": location, "salary_min": salary_min,
           "url": url, "notes": notes, "updated": date.today().isoformat()}
    apps.append(app)
    store.save_apps(apps)
    return f"added {app['id']}: {company} | {role} | {status}"


def update_application(app_id, status=None, notes=None):
    apps = store.load_apps()
    app = next((a for a in apps if a["id"] == app_id), None)
    if not app:
        raise ToolError(f"no application '{app_id}'. ids: {[a['id'] for a in apps]}")
    if status:
        if status not in STATUSES:
            raise ToolError(f"bad status '{status}'. use: {STATUSES}")
        app["status"] = status
    if notes:
        app["notes"] = ((app["notes"] + "; ") if app["notes"] else "") + notes
    app["updated"] = date.today().isoformat()
    store.save_apps(apps)
    return f"updated {app_id}: {app['company']} -> {app['status']}"


def list_applications(status=None, limit=10):
    apps = [a for a in store.load_apps() if not status or a["status"] == status][:limit]
    if not apps:
        return "none"
    return "\n".join(
        f"{a['id']}|{a['company']}|{a['role']}|{a['status']}|{a['work_mode'] or '-'}|{a['updated']}"
        for a in apps)


def save_preference(key, value):
    prefs = store.load_prefs()
    prefs[key] = value
    store.save_prefs(prefs)
    return f"saved {key}={value}"


def get_preferences():
    prefs = store.load_prefs()
    return "; ".join(f"{k}={v}" for k, v in prefs.items()) or "none"


def fetch_job_posting(url):
    """הכלי החיצוני. כתובת שמתחילה ב-fixture: קוראת קובץ מקומי."""
    if url.startswith("fixture:"):
        f = POSTINGS / f"{url[8:]}.txt"
        if not f.exists():
            raise ToolError(f"unknown fixture. have: {[p.stem for p in POSTINGS.glob('*.txt')]}")
        text = f.read_text(encoding="utf-8")
    else:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "jobtrack/1.0"})
            raw = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
        except Exception as e:
            raise ToolError(f"fetch failed: {e}")
        text = re.sub(r"<(script|style).*?</\1>", " ", raw, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_POSTING_CHARS] + (" ...[truncated]" if len(text) > MAX_POSTING_CHARS else "")


def _obj(props, required=()):
    return {"type": "object", "properties": props, "required": list(required)}

TOOLS = [
    {"name": "add_application", "fn": add_application,
     "description": "Record a new job application.",
     "input_schema": _obj({
         "company": {"type": "string"}, "role": {"type": "string"},
         "status": {"type": "string", "enum": STATUSES},
         "work_mode": {"type": "string", "enum": WORK_MODES},
         "location": {"type": "string"}, "salary_min": {"type": "integer"},
         "url": {"type": "string"}, "notes": {"type": "string"}}, ["company", "role"])},
    {"name": "update_application", "fn": update_application,
     "description": "Change status and/or append a note to an existing application.",
     "input_schema": _obj({
         "app_id": {"type": "string"}, "status": {"type": "string", "enum": STATUSES},
         "notes": {"type": "string"}}, ["app_id"])},
    {"name": "list_applications", "fn": list_applications,
     "description": "List applications, optionally filtered by status. One compact line per app.",
     "input_schema": _obj({"status": {"type": "string", "enum": STATUSES},
                           "limit": {"type": "integer"}})},
    {"name": "save_preference", "fn": save_preference,
     "description": "Remember a user job-search preference or decision (e.g. work_mode, min_salary).",
     "input_schema": _obj({"key": {"type": "string"}, "value": {"type": "string"}}, ["key", "value"])},
    {"name": "get_preferences", "fn": get_preferences,
     "description": "Return all saved preferences.",
     "input_schema": _obj({})},
    {"name": "fetch_job_posting", "fn": fetch_job_posting,
     "description": "Fetch a job posting URL and return a short text excerpt.",
     "input_schema": _obj({"url": {"type": "string"}}, ["url"])},
]
TOOLS_BY_NAME = {t["name"]: t for t in TOOLS}
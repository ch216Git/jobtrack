import json, os
from pathlib import Path

def data_dir() -> Path:
    d = Path(os.environ.get("JOBTRACK_DATA_DIR", ".jobtrack_state"))
    d.mkdir(parents=True, exist_ok=True)
    return d

def _load(name, default):
    p = data_dir() / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default
def _save(name, obj):
    (data_dir() / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
def load_apps() -> list: return _load("applications.json", [])
def save_apps(apps: list): _save("applications.json", apps)
def load_prefs() -> dict: return _load("preferences.json", {})
def save_prefs(prefs: dict): _save("preferences.json", prefs)
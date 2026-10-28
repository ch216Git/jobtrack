import os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
tests = sorted(p for p in HERE.glob("*.py") if p.name.startswith(("smoke_", "test_")))

env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
env.pop("ANTHROPIC_API_KEY", None)  # הבדיקות חייבות לעבוד בלי מפתח
env.pop("ANTHROPIC_AUTH_TOKEN", None)

failed = []
for t in tests:
    r = subprocess.run([sys.executable, str(t)], capture_output=True, text=True,
                       encoding="utf-8", cwd=ROOT, env=env)
    ok = r.returncode == 0
    print(f"{'PASS' if ok else 'FAIL'}  {t.name}")
    if not ok:
        failed.append(t.name)
        print("\n".join(r.stderr.strip().splitlines()[-6:]))

print(f"\n{len(tests) - len(failed)}/{len(tests)} test files passed")
sys.exit(1 if failed else 0)
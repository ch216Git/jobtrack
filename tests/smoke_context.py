import os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["JOBTRACK_DATA_DIR"] = tempfile.mkdtemp()

from shared import store
from API.harness import memory, context

store.save_prefs({"work_mode": "remote only", "min_salary": "35000",
                  "decision_acme": "rejected, on-site"})

r = memory.relevant("תוסיפי את המשרה ב-fixture:acme-onsite")
print("onsite request ->", r)
assert "work_mode" in r and "min_salary" not in r

r = memory.relevant("מה המצב שלי ומה העדפות החיפוש?")
print("preferences request ->", r)
assert "work_mode" in r and "min_salary" in r and "decision_acme" in r

r = memory.relevant("מה אני צריכה להכין לראיון?")
print("unrelated request ->", repr(r))
assert r == ""

print(context.user_message("אני רוצה לעבוד מהבית"))
print("ALL OK")
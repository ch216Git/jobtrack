import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
api = json.loads((ROOT / "results" / "api.json").read_text(encoding="utf-8"))
sdk = json.loads((ROOT / "results" / "sdk.json").read_text(encoding="utf-8"))


def agg(r):
    t = r["totals"]
    return {**t, "prompt": t["input"] + t["cache_read"] + t["cache_write"]}


A, S = agg(api), agg(sdk)
pct = lambda a, b: f"{100 * (a - b) / b:+.0f}%"
more = lambda a, b: f"{abs(100 * (a - b) / b):.0f}%"
n = lambda x: f"{x:,.0f}"
cost = lambda x: f"${x:.4f}"


def tools_str(tools):
    return ", ".join(f"{k}×{v}" if v > 1 else k for k, v in Counter(tools).items()) or "-"


def row(label, a, s):
    return f"| {label} | {a} | {s} |"


summary = "\n".join([
    "| מדד (7 תורות, 2 סשנים) | API | SDK |", "|---|---|---|",
    row("input (לא מ-cache)", n(A["input"]), n(S["input"])),
    row("cache read", n(A["cache_read"]), n(S["cache_read"])),
    row("cache write", n(A["cache_write"]), n(S["cache_write"])),
    row("סה״כ טוקני prompt", n(A["prompt"]), n(S["prompt"])),
    row("output", n(A["output"]), n(S["output"])),
    row("אחוז cache", f"{A['cache_hit_pct']}%", f"{S['cache_hit_pct']}%"),
    row("קריאות למודל", n(A["model_calls"]), n(S["model_calls"])),
    row("עלות (USD)", cost(A["cost_usd"]), cost(S["cost_usd"])),
    row("זמן (שניות)", f"{A['seconds']:.0f}", f"{S['seconds']:.0f}"),
    row("בדיקות שעברו", api["checks_passed"], sdk["checks_passed"]),
])

per_turn = ["| תור | API: in / cache read / cache write / out | קריאות | כלים | SDK: in / cache read / cache write / out | קריאות | כלים |",
            "|---|---|---|---|---|---|---|"]
for a, s in zip(api["turns"], sdk["turns"]):
    f = lambda t: f"{t['input']} / {n(t['cache_read'])} / {t['cache_write']} / {t['output']}"
    per_turn.append(f"| {a['id']} | {f(a)} | {a['model_calls']} | {tools_str(a['tools'])} | "
                    f"{f(s)} | {s['model_calls']} | {tools_str(s['tools'])} |")
per_turn = "\n".join(per_turn)

PARTS = ["loop", "tools", "history", "memory", "context", "compaction", "caching", "tokens"]
rep = sdk["loc"]["replaces_by_part"]
loc_rows = ["| חלק | API (שורות קוד) | SDK (שורות עם `# replaces`) |", "|---|---|---|"]
for p in PARTS:
    loc_rows.append(f"| {p} | {api['loc'].get(p, '-')} | {rep.get(p, 0) or 'אוטומטי (0)'} |")
loc_rows.append(f"| **סה״כ** | {api['loc']['total']} (8 קבצי ה-harness) | {rep['total']} מסומנות, מתוך {sdk['loc']['total_sdk_lines']} שורות בכל קבצי ה-SDK |")
loc = "\n".join(loc_rows)

REPORT = f"""# דוח: מעקב חיפוש עבודה, API מול Agent SDK

## הסוכן

סוכן שמנהל חיפוש עבודה: רושם הגשות, מעדכן סטטוס, זוכר העדפות בין סשנים (למשל `work_mode` ו-`min_salary`), וקורא משרה מכתובת. הכלי החיצוני הוא `fetch_job_posting`. בהרצות הוא קורא קבצים מקומיים בכתובות `fixture:`, כדי ששתי הגרסאות יקבלו בדיוק אותו תוכן.

| נושא | איך מומש |
|---|---|
| Tools | 6 כלים ב-`shared/tools.py`: `add_application`, `update_application`, `list_applications`, `save_preference`, `get_preferences`, `fetch_job_posting` (חיצוני) |
| Memory | העדפות והחלטות ב-`preferences.json`. ב-API נשלפות לפי רלוונטיות, וב-SDK נכתבות ל-`CLAUDE.md` |
| Context engineering | ב-API, `context.py` מזריק לכל תור רק העדפות שקשורות לבקשה (בתור t3 לא הוזרק דבר). ב-SDK Claude Code טוען את כל `CLAUDE.md` בתחילת הסשן, והמודל שולף את השאר בכלים |
| Token optimization | פלט כלים קומפקטי (שורה לכל משרה, דף משרה חתוך ל-1,200 תווים), מדידה לכל תור |

**תרחיש:** 7 פניות בשני סשנים. סשן 2 רץ על מופע חדש שנשען רק על מה שנשמר בדיסק. התרחיש כולל שימוש בכלים, שמירה לזיכרון, שליפה בסשן 2, שימוש בכלי החיצוני, ובקשה שסותרת העדפה שמורה (משרה on-site מול "רק remote"). 9 בדיקות pass/fail, ו-8 מהן על המצב בדיסק.

## תנאי ההשוואה

- אותו דגם בשתי הגרסאות: `{api['model']}`, effort `{api['effort']}` (ב-API דרך `output_config`, וב-SDK דרך `effort`).
- גרסאות נעולות: `anthropic==2.3.0`, `claude-agent-sdk==0.2.174` (ב-`requirements.txt`).
- כל ריצה מתחילה ממצב נקי (מצב הדיסק נמחק).
- **שתי הגרסאות חויבו מאותו מפתח API.** ה-SDK לא רץ על מנוי, כדי שהעלויות יהיו ברות השוואה.
- הערה על ה-cache: את ה-prompt cache בצד השרת אי אפשר לנקות. ריצות קודמות (ניסיון כושל של ה-API ובדיקת חיבור של ה-SDK) יכלו לחמם אותו, ולכן ה-cache read בתור הראשון בשתי הגרסאות לא מייצג התחלה קרה.

## 1. תוצאות

{summary}

עלות כוללת מאומתת מול Console: ______ (למלא אחרי בדיקת Usage ב-Console).

פירוט לפי תור:

{per_turn}

## 2. שורות קוד לכל חלק ב-harness

{loc}

ספירה: שורות קוד בלבד, בלי שורות ריקות והערות. ב-SDK החלקים `compaction` ו-`caching` אוטומטיים, ולכן אין להם שורות.

## 3. איפה ה-SDK עלה יותר טוקנים, ואיפה פחות

- **סה״כ טוקני prompt:** ה-SDK שלח {n(S['prompt'])} מול {n(A['prompt'])} ב-API ({pct(S['prompt'], A['prompt'])}). Claude Code מוסיף לבקשה הקשר משלו (מידע על הסביבה, תיאורי כלים בפורמט `mcp__jobtrack__*`, ו-`CLAUDE.md`), גם כשמחליפים את ה-system prompt.
- **קריאות למודל:** {S['model_calls']:.0f} ב-SDK מול {A['model_calls']:.0f} ב-API. בתורות שבהם המודל קרא לשני כלים (למשל t1, t4 ו-t7), ה-API קיבל את שתי הקריאות בהודעה אחת ושלח את שתי התוצאות יחד, ואילו ב-SDK נרשמו קריאה אחת נוספת בכל אחד מהם. סביר שה-SDK הפעיל את הכלים בזה אחר זה, אבל זו הסקה שלי: `num_turns` לא תועד לי במדויק, ולא בדקתי אותו מול הודעות הביניים.
- **cache:** שתי הגרסאות הגיעו לאחוז cache דומה ({A['cache_hit_pct']}% ב-API, {S['cache_hit_pct']}% ב-SDK). ב-SDK נכתבו יותר טוקנים ל-cache ({n(S['cache_write'])} מול {n(A['cache_write'])}), כנראה בגלל פרפיקס גדול יותר.
- **output:** כמעט זהה ({n(S['output'])} מול {n(A['output'])}), כך שההבדל העיקרי הוא בקלט ולא בפלט.
- **עלות:** {cost(S['cost_usd'])} ב-SDK מול {cost(A['cost_usd'])} ב-API ({pct(S['cost_usd'], A['cost_usd'])}).
- **זמן:** {S['seconds']:.0f} שניות מול {A['seconds']:.0f}. ב-SDK כל תור מפעיל תהליך Claude Code חדש עם `resume`, וזה כנראה חלק מההפרש.

**הסתייגות:** זו ריצה אחת לכל גרסה, והמודל לא דטרמיניסטי: מספר הקריאות והכלים משתנה מריצה לריצה. ההבדלים כאן הם סדרי גודל ולא מדידה מדויקת.

## 4. על מה הייתה לי שליטה ב-API ואיבדתי ב-SDK

- **מה נכנס לכל תור.** ב-API שלפתי רק העדפות רלוונטיות, ובתור t3 לא הוזרק זיכרון בכלל. ב-SDK נטען כל `CLAUDE.md` בתחילת הסשן. בתרחיש הקטן הזה ההבדל זעיר (יש רק שתי העדפות), אבל בזיכרון גדול הוא היה מורגש.
- **Caching.** ב-API קבעתי בעצמי את נקודות ה-cache. ב-SDK זה אוטומטי, ובפועל הוא הגיע לתוצאה דומה, כך שבתרחיש הזה לא הפסדתי כלום.
- **Compaction.** ב-API קבעתי את הסף ואת ה-prompt של הסיכום. בשתי הריצות הסף לא הופעל, ולכן את ה-compaction בדקתי רק offline.
- **קריאות כלים.** ב-API הכלים רצים יחד בהודעה אחת. ב-SDK אני לא שולטת בסדר ובמקביליות.
- **מדידת עלות.** ב-API יש `usage` מדויק לכל קריאה. ב-SDK הטוקנים לכל תור מדויקים, אבל `total_cost_usd` **מצטבר לאורך הסשן עם `resume`**. את זה גיליתי רק בהרצה: בלי תיקון, העלות שדווחה הייתה $0.2018, כמעט פי שניים מהעלות האמיתית. התיקון הוא חישוב הפרשים בין תורות.
- **thinking.** ב-Opus 5.5 צריך להחזיר בלוקי thinking לשרת במלואם בלולאת כלים. ב-API הייתי צריכה לטפל בזה בעצמי ב-`loop.py`, ובלי זה ההרצה האמיתית הייתה נכשלת. ב-SDK זה מטופל אוטומטית.
- **תלות בסביבה.** ה-SDK כולל תוכנת Claude Code בגודל כ-300MB שרצה כתהליך נפרד.

## 5. איזו גרסה הייתי בוחרת לסוכן הזה

**SDK, לשימוש אישי.** שתי הגרסאות עברו את כל הבדיקות, כך שהבחירה היא על מאמץ ושליטה. ה-SDK עלה בכ-{more(S['cost_usd'], A['cost_usd'])} יותר, אבל חסך את הלולאה, ההיסטוריה, ה-caching, ה-compaction וטיפול בבלוקי thinking, וזה הרבה פחות קוד לכתוב ולתחזק. סוכן אישי עם כמה כלים וסשנים קצרים לא צריך שליטה ברמת הבקשה.

הייתי בוחרת ב-API אם הסוכן היה שירות לכמה משתמשים, אם חשובה עלות או latency נמוכים, אם צריך זיכרון גדול שנשלף לפי רלוונטיות, או אם אי אפשר להריץ את Claude Code בסביבה.

## 6. מגבלות

- ריצה אחת לכל גרסה, ללא חזרות.
- ה-cache בשרת לא נוקה בין ריצות.
- compaction לא הופעל באף אחת מהריצות.
- `num_turns` של ה-SDK הוא ההנחה שלי לגבי מספר הקריאות למודל.
"""
(ROOT / "REPORT.md").write_text(REPORT, encoding="utf-8")
print("wrote REPORT.md")
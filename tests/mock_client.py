from types import SimpleNamespace as NS

USAGE = NS(input_tokens=300, output_tokens=40,
           cache_read_input_tokens=0, cache_creation_input_tokens=0)
_counter = [0]


def tu(name, **inp):
    _counter[0] += 1
    return NS(type="tool_use", id=f"id{_counter[0]}", name=name, input=inp)


def tool_resp(*blocks):
    return NS(stop_reason="tool_use", usage=USAGE, content=list(blocks))


def text_resp(text):
    return NS(stop_reason="end_turn", usage=USAGE, content=[NS(type="text", text=text)])


class ScriptedClient:
    def __init__(self, script):
        self.script, self.calls, self.messages = script, [], self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.script[len(self.calls) - 1]


# סוכן "מושלם" לתרחיש שלנו: 14 קריאות למודל בסך הכול
PERFECT_SCRIPT = [
    # t1
    tool_resp(tu("save_preference", key="work_mode", value="remote"),
              tu("save_preference", key="min_salary", value="35000")),
    text_resp("נשמר."),
    # t2
    tool_resp(tu("fetch_job_posting", url="fixture:globex-remote")),
    tool_resp(tu("add_application", company="Globex", role="Senior Python Developer",
                 work_mode="remote", status="applied")),
    text_resp("רשמתי את ההגשה ל-Globex."),
    # t3
    tool_resp(tu("update_application", app_id="a1", status="screening")),
    text_resp("עודכן ל-screening."),
    # t4 (סשן 2)
    text_resp("העדפות: remote only, שכר מינימום 35000. Globex בסטטוס screening."),
    # t5: הסתירה, בלי לרשום
    tool_resp(tu("fetch_job_posting", url="fixture:acme-onsite")),
    text_resp("המשרה on-site וזה סותר את ההעדפה remote. לרשום בכל זאת?"),
    # t6: אישור
    tool_resp(tu("add_application", company="Acme Robotics", role="Backend Engineer",
                 work_mode="onsite", status="saved")),
    text_resp("נרשם בסטטוס saved."),
    # t7
    tool_resp(tu("update_application", app_id="a2", status="withdrawn"),
              tu("save_preference", key="decision_acme", value="withdrawn: on-site")),
    text_resp("עודכן ונשמר."),
]
import json
from . import say, history

SUMMARY_PROMPT = (
    "Summarize this conversation for a job-search assistant that will continue it. "
    "Keep: user decisions and their reasons, preferences, application ids and companies, open questions. "
    "Max 150 words. Plain text, no preamble.")


def estimate_tokens(messages):
    """הערכה גסה: תווים חלקי 3. מספיקה כדי להחליט מתי לסכם."""
    return len(json.dumps(messages, ensure_ascii=False)) // 3


def maybe_compact(client, model, messages, session_id, meter, threshold=6000, **extra):
    est = estimate_tokens(messages)
    if est < threshold:
        return messages
    say("compaction.py", f"~{est} tokens >= {threshold}: summarizing {len(messages)} messages")
    response = client.messages.create(
        model=model, max_tokens=500, system=SUMMARY_PROMPT,
        messages=messages + [{"role": "user", "content": "Summarize the conversation so far."}],
        **extra)
    meter.add_call(response.usage)
    text = "".join(b.text for b in response.content if b.type == "text")
    new_messages = [
        {"role": "user", "content": f"<summary>{text}</summary>"},
        {"role": "assistant", "content": "Understood."}]
    history.append_compaction(session_id, new_messages)
    say("compaction.py", f"compacted {len(messages)} messages into {len(new_messages)}")
    return new_messages
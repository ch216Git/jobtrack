from . import tools as harness_tools
from . import say, history, caching

def _blocks_to_dicts(content):
    """ממיר את תשובת המודל למילונים לשמירה בדיסק. בלוקי thinking נשמרים כמו שהם."""
    out = []
    for b in content:
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
        elif b.type == "thinking":
            out.append({"type": "thinking", "thinking": b.thinking, "signature": b.signature})
        elif b.type == "redacted_thinking":
            out.append({"type": "redacted_thinking", "data": b.data})
    return out


def run_turn(client, model, system, messages, session_id, meter, tool_schemas,
             max_iterations=10, max_tokens=2000, **extra):
    """מריץ תור אחד. messages כבר כולל את הודעת ה-user החדשה. מחזיר את הטקסט הסופי."""
    for i in range(max_iterations):
        response = client.messages.create(
            model=model, max_tokens=max_tokens,
            system=caching.system_blocks(system),
            tools=caching.tools_with_cache(tool_schemas),
            messages=caching.messages_with_cache(messages), **extra)
        meter.add_call(response.usage)
        say("loop.py", f"model call {i + 1}: stop_reason={response.stop_reason}")

        assistant_msg = {"role": "assistant", "content": _blocks_to_dicts(response.content)}
        messages.append(assistant_msg)
        history.append(session_id, assistant_msg)

        if response.stop_reason != "tool_use":
            return "".join(b["text"] for b in assistant_msg["content"] if b["type"] == "text")

        for b in response.content:
            if b.type == "tool_use":
                meter.add_tool(b.name)
        results_msg = harness_tools.run_tool_calls(response.content)
        messages.append(results_msg)
        history.append(session_id, results_msg)

    say("loop.py", "stopped: too many tool iterations")
    return "[stopped: too many tool iterations]"
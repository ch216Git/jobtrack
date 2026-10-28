import json
from shared.tools import TOOLS, TOOLS_BY_NAME, ToolError
from . import say


def schemas():
    """רשימת הכלים בפורמט שה-API מצפה לו (בלי הפונקציה עצמה)."""
    return [{"name": t["name"], "description": t["description"],
             "input_schema": t["input_schema"]} for t in TOOLS]


def run_tool(name, tool_input):
    """מפעיל כלי אחד ומחזיר (טקסט, is_error)."""
    tool = TOOLS_BY_NAME.get(name)
    if tool is None:
        say("tools.py", f"unknown tool {name}")
        return f"unknown tool '{name}'. available: {list(TOOLS_BY_NAME)}", True
    try:
        result = tool["fn"](**tool_input)
        say("tools.py", f"ran {name}({json.dumps(tool_input, ensure_ascii=False)})")
        return str(result), False
    except ToolError as e:
        say("tools.py", f"{name} failed: {e}")
        return str(e), True
    except TypeError as e:
        say("tools.py", f"{name} bad arguments: {e}")
        return f"bad arguments for {name}: {e}", True


def run_tool_calls(content_blocks):
    """לכל בלוק tool_use יוצר tool_result. כולם חוזרים יחד בהודעת user אחת."""
    results = []
    for block in content_blocks:
        if block.type == "tool_use":
            text, is_error = run_tool(block.name, block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": text, "is_error": is_error})
    return {"role": "user", "content": results}
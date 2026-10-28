import argparse, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import scenario as sc
from API.agent import Agent

HARNESS = ["loop", "tools", "history", "memory", "context", "compaction", "caching", "tokens"]


def effort_params(effort):
    return {"output_config": {"effort": effort}} if effort else {}


def run_api(client, scn, state_dir):
    shutil.rmtree(state_dir, ignore_errors=True)  # כל ריצה מתחילה ממצב נקי
    os.environ["JOBTRACK_DATA_DIR"] = str(state_dir)
    model = scn["model"]
    extra = effort_params(scn.get("effort"))

    def new_session(session_id):
        return Agent(client, model, session_id, extra=extra).handle

    order, checks = sc.run(scn, new_session)
    files = {n: ROOT / "API" / "harness" / f"{n}.py" for n in HARNESS}
    return {
        "harness": "api", "model": model, "effort": scn.get("effort"),
        "turns": order, "totals": sc.totals(order), "checks": checks,
        "checks_passed": f"{sum(c['passed'] for c in checks)}/{len(checks)}",
        "loc": sc.loc_report(files),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    import anthropic  # קורא את ANTHROPIC_API_KEY ממשתנה הסביבה
    scn = sc.load(args.scenario)
    result = run_api(anthropic.Anthropic(), scn, ROOT / ".run_state" / "api")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[main.py] wrote {out} | checks {result['checks_passed']} | "
          f"cost ${result['totals']['cost_usd']}")


if __name__ == "__main__":
    main()
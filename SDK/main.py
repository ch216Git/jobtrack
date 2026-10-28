import argparse, json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared import scenario as sc
from SDK.agent import Agent

SDK_FILES = ["agent.py", "tools.py", "main.py"]


def run_sdk(scn, state_dir, client_factory=None):
    shutil.rmtree(state_dir, ignore_errors=True)  # כל ריצה מתחילה ממצב נקי
    os.environ["JOBTRACK_DATA_DIR"] = str(state_dir)
    kwargs = {"client_factory": client_factory} if client_factory else {}

    def new_session(session_id):
        return Agent(scn["model"], scn.get("effort"), **kwargs).handle

    order, checks = sc.run(scn, new_session)
    paths = [ROOT / "SDK" / f for f in SDK_FILES]
    return {
        "harness": "sdk", "model": scn["model"], "effort": scn.get("effort"),
        "turns": order, "totals": sc.totals(order), "checks": checks,
        "checks_passed": f"{sum(c['passed'] for c in checks)}/{len(checks)}",
        "loc": {"replaces_by_part": sc.replaces_report(paths),
                "total_sdk_lines": sum(sc.count_lines(p) for p in paths)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    result = run_sdk(sc.load(args.scenario), ROOT / ".run_state" / "sdk")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SDK/main.py] wrote {out} | checks {result['checks_passed']} | "
          f"cost ${result['totals']['cost_usd']}")


if __name__ == "__main__":
    main()
"""Re-grade saved agent outputs with the current hidden tests (no agent rerun).

    uv run --project app python analysis/rescore.py <job_dir> [-o analysis/rescored_<job>.csv]

Each trial saved the app the agent produced (artifacts/app). This copies the trial's task
tests, swaps in the current test_hidden_<feature>.py files from task_src/, runs them
against that saved app, and records old vs new reward. Use it when a grader bug is fixed,
so every agent's outputs are re-graded by exactly the same tests.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "task_src"
TASKS = ROOT / "tasks"


def rescore_trial(trial: Path) -> dict:
    task = json.loads((trial / "result.json").read_text(encoding="utf-8"))["task_name"]
    old = float((trial / "verifier" / "reward.txt").read_text().strip() or 0)
    with tempfile.TemporaryDirectory() as tmp:
        tests = Path(tmp) / "tests"
        shutil.copytree(TASKS / task / "tests", tests, ignore=shutil.ignore_patterns("__pycache__"))
        for hidden in tests.glob("test_hidden_*.py"):
            feature = hidden.stem.removeprefix("test_hidden_").replace("_", "-")
            if (SRC / feature / "test_hidden.py").is_file():
                shutil.copy2(SRC / feature / "test_hidden.py", hidden)
        if (tests / "test_hidden_conventions.py").is_file():
            shutil.copy2(SRC / "_common" / "test_hidden_conventions.py", tests / "test_hidden_conventions.py")
        junit = Path(tmp) / "junit.xml"
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
             f"--junitxml={junit}", str(tests)],
            env={**os.environ, "PYTHONPATH": str((trial / "artifacts" / "app").resolve())},
            cwd=tests, capture_output=True,
        )
        out = subprocess.run([sys.executable, str(tests / "score.py"), str(junit), tmp],
                             capture_output=True, text=True, check=True).stdout
        new = json.loads(out.strip().splitlines()[-1])
        failed = sorted({
            f"{case.get('classname', '').split('.')[-1].removeprefix('test_hidden_')}::{case.get('name', '').split('[')[0]}"
            for case in ET.parse(junit).iter("testcase") if any(c.tag in ("failure", "error") for c in case)
        }) if junit.is_file() else ["<no junit>"]
    return {"trial": trial.name, "task": task, "old_reward": old, "new_reward": new["reward"],
            "hidden_passed": new["hidden_passed"], "hidden_total": new["hidden_total"],
            "regression_passed": new["regression_passed"], "regression_total": new["regression_total"],
            "failed_tests": "; ".join(failed)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("job", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()
    trials = sorted(p for p in args.job.iterdir() if (p / "artifacts" / "app").is_dir() and (p / "verifier" / "reward.txt").is_file())
    rows = [rescore_trial(t) for t in trials]
    out = args.output or ROOT / "analysis" / f"rescored_{args.job.name}.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for r in rows:
        flag = "" if r["old_reward"] == r["new_reward"] else "  <- changed"
        print(f"{r['trial']:45} old={r['old_reward']:.3f}  new={r['new_reward']:.3f}{flag}")
        if r["failed_tests"]:
            print(f"{'':47}still failing: {r['failed_tests']}")
    n = len(rows)
    old_full = sum(r["old_reward"] == 1.0 for r in rows)
    new_full = sum(r["new_reward"] == 1.0 for r in rows)
    print(f"\n{n} trials | full-pass: {old_full}/{n} -> {new_full}/{n} | "
          f"mean reward: {sum(r['old_reward'] for r in rows) / n:.3f} -> {sum(r['new_reward'] for r in rows) / n:.3f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

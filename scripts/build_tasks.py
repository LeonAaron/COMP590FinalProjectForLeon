"""Generate Harbor task folders from task_src/ and (optionally) validate them locally.

    uv run --project app python scripts/build_tasks.py           # (re)build tasks/
    uv run --project app python scripts/build_tasks.py --check   # build + local oracle/nop check

Each task_src/<feature>/ holds instruction.md, test_hidden.py and solution.py for ONE
feature. A task (see TASKS below) bundles several features into one release: its
instruction is the shared preamble plus each feature's description, its hidden tests are
each feature's test file, and its reference solution applies each feature's patch in order.
Everything else is shared (task_src/_common) or copied from app/, so every task starts
from the identical baseline app.

v1 (git history, prefix leoa_stock_) had one feature per task with fully enumerated
edge cases; the baseline agent scored 1.0 on all of them, so v2 bundles 3 features per
task and moves edge-case rules into shared codebase conventions.

v2 (prefix leoa_stock2_): with fair grading the baseline passed every held-out release;
its only real misses (dev) were rules stated once in the shared conventions. v3 (this
version, prefix leoa_stock3_) adds codebase-wide conventions (no-store API caching, page
titles, shared header, table captions, panel aria-labels) checked on every feature by
_common/test_hidden_conventions.py, driven by each feature's conventions.json.

--check runs, for every task and without Docker:
  * oracle: copy app -> apply the reference solution -> score must be 1.0
  * nop:    copy app untouched                       -> score must be 0.0
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
SRC = ROOT / "task_src"
COMMON = SRC / "_common"
OUT = ROOT / "tasks"
PREFIX = "leoa_stock3_"

# task name -> (split, features). Dev tasks only use dev features, so nothing about the
# held-out features leaks into development of the multi-agent harness.
TASKS: dict[str, tuple[str, list[str]]] = {
    "price-insights": ("dev", ["daily-change", "moving-average", "watchlist"]),
    "personal-dashboard": ("dev", ["top-movers", "watchlist", "daily-change"]),
    "analytics-suite": ("heldout", ["dashboard", "analysis-report", "csv-export"]),
    "power-tools": ("heldout", ["date-range", "compare", "price-alerts"]),
    "research-tools": ("heldout", ["analysis-report", "date-range", "price-alerts"]),
    "market-overview": ("heldout", ["dashboard", "compare", "csv-export"]),
}

IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".venv", "*.pyc")


def copy_app(dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copytree(APP / "stockapp", dest / "stockapp", ignore=IGNORE)
    shutil.copytree(APP / "tests", dest / "tests", ignore=IGNORE)
    for name in ("pyproject.toml", "README.md"):
        shutil.copy2(APP / name, dest / name)


def write_lf(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def build_task(name: str) -> Path:
    split, features = TASKS[name]
    task = OUT / f"{PREFIX}{name}"
    if task.exists():
        shutil.rmtree(task)
    read = lambda path: path.read_text(encoding="utf-8")  # noqa: E731

    write_lf(task / "task.toml", read(COMMON / "task.toml").replace("{split}", split))
    write_lf(
        task / "instruction.md",
        read(COMMON / "preamble.md")
        + "\n\n".join(read(SRC / f / "instruction.md").strip() for f in features)
        + "\n",
    )

    write_lf(task / "environment" / "Dockerfile", read(COMMON / "Dockerfile"))
    copy_app(task / "environment" / "app")

    tests = task / "tests"
    write_lf(tests / "test.sh", read(COMMON / "test.sh"))
    write_lf(tests / "score.py", read(COMMON / "score.py"))
    write_lf(tests / "conftest.py", read(APP / "tests" / "conftest.py"))
    for original in sorted((APP / "tests").glob("test_*.py")):
        write_lf(tests / f"test_regression_{original.name[5:]}", read(original))

    sol = task / "solution"
    write_lf(sol / "solve.sh", '#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\npython3 solution.py\n')
    write_lf(sol / "patchlib.py", read(COMMON / "patchlib.py"))
    runner = ["import runpy", ""]
    conventions: dict = {"api": [], "pages": {}, "tables": {}, "sections": []}
    for feature in features:
        module = feature.replace("-", "_")
        write_lf(tests / f"test_hidden_{module}.py", read(SRC / feature / "test_hidden.py"))
        write_lf(sol / f"sol_{module}.py", read(SRC / feature / "solution.py"))
        runner.append(f'runpy.run_path("sol_{module}.py")')
        extra = json.loads(read(SRC / feature / "conventions.json"))
        conventions["api"] += [u for u in extra.get("api", []) if u not in conventions["api"]]
        conventions["pages"].update(extra.get("pages", {}))
        conventions["tables"].update(extra.get("tables", {}))
        conventions["sections"] += [s for s in extra.get("sections", []) if s not in conventions["sections"]]
    write_lf(sol / "solution.py", "\n".join(runner) + "\n")
    write_lf(tests / "test_hidden_conventions.py", read(COMMON / "test_hidden_conventions.py"))
    write_lf(tests / "conventions.json", json.dumps(conventions, indent=2) + "\n")
    return task


def run_score(task: Path, app_dir: Path) -> dict:
    """Mirror tests/test.sh against a local app copy."""
    with tempfile.TemporaryDirectory() as tmp:
        junit = Path(tmp) / "junit.xml"
        env = {**os.environ, "PYTHONPATH": str(app_dir)}
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=",
             f"--junitxml={junit}", str(task / "tests")],
            env=env, cwd=task / "tests", capture_output=True, text=True,
        )
        subprocess.run(
            [sys.executable, str(task / "tests" / "score.py"), str(junit), tmp],
            capture_output=True, text=True, check=True,
        )
        return json.loads((Path(tmp) / "scores.json").read_text(encoding="utf-8"))


def check(task: Path) -> bool:
    ok = True
    with tempfile.TemporaryDirectory() as tmp:
        nop = Path(tmp) / "nop"
        copy_app(nop)
        nop_score = run_score(task, nop)

        oracle = Path(tmp) / "oracle"
        copy_app(oracle)
        proc = subprocess.run(
            [sys.executable, "solution.py"], cwd=task / "solution",
            env={**os.environ, "APP_DIR": str(oracle)}, capture_output=True, text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout, proc.stderr)
            ok = False
        oracle_score = run_score(task, oracle)

    ok = ok and oracle_score["reward"] == 1.0 and nop_score["reward"] == 0.0
    print(
        f"{'OK ' if ok else 'BAD'} {task.name:32} "
        f"oracle={oracle_score['reward']:.3f} ({oracle_score['hidden_passed']}/{oracle_score['hidden_total']} hidden, "
        f"{oracle_score['regression_passed']}/{oracle_score['regression_total']} regr)  "
        f"nop={nop_score['reward']:.3f} ({nop_score['hidden_passed']}/{nop_score['hidden_total']} hidden)"
    )
    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate oracle=1 and nop=0 locally")
    parser.add_argument("names", nargs="*", help=f"only these tasks (default all: {', '.join(TASKS)})")
    args = parser.parse_args()

    names = args.names or list(TASKS)
    if not args.names and OUT.exists():
        shutil.rmtree(OUT)  # full rebuild: drop tasks that are no longer defined
    built = [build_task(name) for name in names]
    print(f"built {len(built)} task(s) in {OUT.relative_to(ROOT)}/")
    if args.check and not all([check(t) for t in built]):
        sys.exit(1)


if __name__ == "__main__":
    main()

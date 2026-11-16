"""Generate Harbor task folders from task_src/ and (optionally) validate them locally.

    uv run --project app python scripts/build_tasks.py           # (re)build tasks/
    uv run --project app python scripts/build_tasks.py --check   # build + local oracle/nop check

Each task_src/<name>/ holds instruction.md, test_hidden.py and solution.py. Everything
else is shared (task_src/_common) or copied from app/, so every task starts from the
identical baseline app.

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
PREFIX = "leoa_stock_"

DEV = {"daily-change", "watchlist", "moving-average"}

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


def build_task(src: Path) -> Path:
    name = src.name
    task = OUT / f"{PREFIX}{name}"
    if task.exists():
        shutil.rmtree(task)
    split = "dev" if name in DEV else "heldout"

    write_lf(task / "task.toml", (COMMON / "task.toml").read_text(encoding="utf-8").replace("{split}", split))
    write_lf(
        task / "instruction.md",
        (COMMON / "preamble.md").read_text(encoding="utf-8") + (src / "instruction.md").read_text(encoding="utf-8"),
    )

    write_lf(task / "environment" / "Dockerfile", (COMMON / "Dockerfile").read_text(encoding="utf-8"))
    copy_app(task / "environment" / "app")

    tests = task / "tests"
    write_lf(tests / "test.sh", (COMMON / "test.sh").read_text(encoding="utf-8"))
    write_lf(tests / "score.py", (COMMON / "score.py").read_text(encoding="utf-8"))
    write_lf(tests / "conftest.py", (APP / "tests" / "conftest.py").read_text(encoding="utf-8"))
    for original in sorted((APP / "tests").glob("test_*.py")):
        write_lf(tests / f"test_regression_{original.name[5:]}", original.read_text(encoding="utf-8"))
    write_lf(tests / "test_hidden.py", (src / "test_hidden.py").read_text(encoding="utf-8"))

    sol = task / "solution"
    write_lf(
        sol / "solve.sh",
        '#!/bin/bash\nset -euo pipefail\ncd "$(dirname "$0")"\npython3 solution.py\n',
    )
    write_lf(sol / "solution.py", (src / "solution.py").read_text(encoding="utf-8"))
    write_lf(sol / "patchlib.py", (COMMON / "patchlib.py").read_text(encoding="utf-8"))
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
    parser.add_argument("names", nargs="*", help="only these task_src names")
    args = parser.parse_args()

    sources = sorted(p for p in SRC.iterdir() if p.is_dir() and not p.name.startswith("_"))
    if args.names:
        sources = [p for p in sources if p.name in args.names]
    tasks = [build_task(src) for src in sources]
    print(f"built {len(tasks)} task(s) in {OUT.relative_to(ROOT)}/")
    if args.check and not all([check(t) for t in tasks]):
        sys.exit(1)


if __name__ == "__main__":
    main()

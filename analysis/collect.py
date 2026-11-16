"""Collect Harbor trial results into one CSV and print a per-agent summary.

    python analysis/collect.py <job_dir> [<job_dir> ...] [-o analysis/results.csv]
        [--price-in 1.25 --price-cached 0.125 --price-out 10]   # USD per 1M tokens (optional)

One row per trial. Columns:
  job, agent, task, split (dev/heldout), trial, reward, hidden_passed, hidden_total,
  regression_passed, regression_total, input_tokens, cached_tokens, output_tokens,
  total_tokens, turns, agent_seconds, trial_seconds, cost_usd, exception, infra_error

Trials that died because the model gateway failed (HTTP 5xx, rate limit, connection or
timeout errors from the OpenAI client) are flagged infra_error=1. They say nothing about
the agent's ability, so the summary excludes them and reports how many there were; they
should be rerun. They stay in the CSV so nothing is silently dropped.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEV = {
    # v1 (single-feature tasks)
    "leoa_stock_daily-change", "leoa_stock_watchlist", "leoa_stock_moving-average",
    # v2 (three-feature releases)
    "leoa_stock2_price-insights", "leoa_stock2_personal-dashboard",
}

INFRA_MARKERS = (
    "InternalServerError", "RateLimitError", "APIConnectionError", "APITimeoutError",
    "ServiceUnavailable", "Error code: 5",
)

FIELDS = [
    "job", "agent", "task", "split", "trial", "reward", "hidden_passed", "hidden_total",
    "regression_passed", "regression_total", "input_tokens", "cached_tokens", "output_tokens",
    "total_tokens", "turns", "agent_seconds", "trial_seconds", "cost_usd", "exception", "infra_error",
]


def seconds(span: dict | None) -> float | None:
    if not span or not span.get("started_at") or not span.get("finished_at"):
        return None
    start = datetime.fromisoformat(span["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(span["finished_at"].replace("Z", "+00:00"))
    return round((end - start).total_seconds(), 1)


def count_turns(trial: Path) -> int:
    text = ""
    for name in ("stdout.txt", "stderr.txt"):
        path = trial / "agent" / name
        if path.is_file():
            text += path.read_text(encoding="utf-8", errors="replace")
    return text.count("TRACE {")


def trial_row(job: Path, trial: Path, prices: tuple[float, float, float] | None) -> dict:
    result = json.loads((trial / "result.json").read_text(encoding="utf-8"))
    agent_result = result.get("agent_result") or {}
    scores_path = trial / "verifier" / "scores.json"
    scores = json.loads(scores_path.read_text()) if scores_path.is_file() else {}
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}

    n_in = agent_result.get("n_input_tokens") or 0
    n_cached = agent_result.get("n_cache_tokens") or 0
    n_out = agent_result.get("n_output_tokens") or 0
    cost = None
    if prices:
        p_in, p_cached, p_out = prices
        cost = round(((n_in - n_cached) * p_in + n_cached * p_cached + n_out * p_out) / 1e6, 5)

    task = result["task_name"]
    kwargs = ((result.get("config") or {}).get("agent") or {}).get("kwargs") or {}
    exc = result.get("exception_info")
    return {
        "job": job.name,
        "agent": kwargs.get("agent") or (result.get("agent_info") or {}).get("name"),
        "task": task,
        "split": "dev" if task in DEV else "heldout",
        "trial": result["trial_name"],
        "reward": rewards.get("reward", 0.0),
        "hidden_passed": scores.get("hidden_passed"),
        "hidden_total": scores.get("hidden_total"),
        "regression_passed": scores.get("regression_passed"),
        "regression_total": scores.get("regression_total"),
        "input_tokens": n_in,
        "cached_tokens": n_cached,
        "output_tokens": n_out,
        "total_tokens": n_in + n_out,
        "turns": count_turns(trial),
        "agent_seconds": seconds(result.get("agent_execution")),
        "trial_seconds": seconds(result),
        "cost_usd": cost,
        "exception": (exc or {}).get("exception_type") if isinstance(exc, dict) else (exc or ""),
        "infra_error": int(
            isinstance(exc, dict)
            and any(m in (exc.get("exception_message") or "") for m in INFRA_MARKERS)
        ),
    }


def summarize(rows: list[dict]) -> None:
    infra = [r for r in rows if r["infra_error"]]
    if infra:
        print(f"\nexcluded {len(infra)} trial(s) lost to model-gateway errors (rerun these):")
        for r in infra:
            print(f"  {r['agent']:18} {r['trial']}")
    rows = [r for r in rows if not r["infra_error"]]
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["agent"], r["split"])].append(r)
        groups[(r["agent"], "all")].append(r)

    def fmt(values: list[float], pct: bool = False) -> str:
        if not values:
            return "-"
        mean = statistics.mean(values)
        sd = statistics.stdev(values) if len(values) > 1 else 0.0
        return f"{mean * 100:5.1f}% +/-{sd * 100:4.1f}" if pct else f"{mean:9.0f} +/-{sd:7.0f}"

    print(f"\n{'agent':18} {'split':8} {'n':>3}  {'reward (mean +/- sd)':>18}  {'full pass':>9}  "
          f"{'tokens/trial':>18}  {'agent sec':>16}")
    for (agent, split), rs in sorted(groups.items()):
        rewards = [r["reward"] for r in rs]
        full = sum(1 for r in rs if r["reward"] == 1.0)
        print(f"{agent:18} {split:8} {len(rs):3}  {fmt(rewards, pct=True):>18}  {full:4}/{len(rs):<4}  "
              f"{fmt([r['total_tokens'] for r in rs]):>18}  {fmt([r['agent_seconds'] or 0 for r in rs]):>16}")

    print("\nper task (mean reward over attempts):")
    by_task: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in rows:
        by_task[(r["agent"], r["task"])].append(r["reward"])
    for (agent, task), rewards in sorted(by_task.items()):
        print(f"  {agent:18} {task:32} {statistics.mean(rewards):.3f}  {[round(x, 3) for x in rewards]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("jobs", nargs="+", type=Path)
    parser.add_argument("-o", "--output", type=Path, default=Path(__file__).parent / "results.csv")
    parser.add_argument("--price-in", type=float)
    parser.add_argument("--price-cached", type=float)
    parser.add_argument("--price-out", type=float)
    args = parser.parse_args()
    prices = (args.price_in, args.price_cached, args.price_out) if args.price_in is not None else None

    rows = [
        trial_row(job, trial, prices)
        for job in args.jobs
        for trial in sorted(p for p in job.iterdir() if (p / "result.json").is_file())
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {args.output}")
    summarize(rows)


if __name__ == "__main__":
    main()

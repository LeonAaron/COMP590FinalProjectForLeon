"""Turn a pytest JUnit report into a partial-credit reward.

reward = (hidden tests passed / hidden total) * (regression tests passed / regression total)

Hidden tests check the requested feature. Regression tests are the app's original
tests, so breaking existing behaviour scales the reward down. The untouched app
scores 0 because it passes no hidden tests.

Usage: python score.py <junit.xml> <output_dir>
Writes <output_dir>/reward.txt and <output_dir>/scores.json.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def score(junit: Path) -> dict[str, float | int]:
    counts = {"hidden": [0, 0], "regression": [0, 0]}
    if junit.is_file():
        for case in ET.parse(junit).iter("testcase"):
            group = "regression" if "test_regression" in case.get("classname", "") else "hidden"
            failed = any(child.tag in ("failure", "error", "skipped") for child in case)
            counts[group][1] += 1
            counts[group][0] += 0 if failed else 1
    hidden_frac = counts["hidden"][0] / counts["hidden"][1] if counts["hidden"][1] else 0.0
    regression_frac = (
        counts["regression"][0] / counts["regression"][1] if counts["regression"][1] else 0.0
    )
    return {
        "reward": round(hidden_frac * regression_frac, 4),
        "hidden_passed": counts["hidden"][0],
        "hidden_total": counts["hidden"][1],
        "regression_passed": counts["regression"][0],
        "regression_total": counts["regression"][1],
    }


def main() -> None:
    junit, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    result = score(junit)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "reward.txt").write_text(f"{result['reward']}\n")
    (out_dir / "scores.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()

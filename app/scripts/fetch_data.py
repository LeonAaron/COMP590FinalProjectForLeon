"""One-time snapshot of daily prices into stockapp/data/<TICKER>.csv.

The app never calls an API at runtime: evaluations must be deterministic and
the Harbor sandboxes have no network. Re-run this only to refresh the snapshot.

    python scripts/fetch_data.py
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stockapp.stocks import DATA_DIR, TICKERS  # noqa: E402

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1y&interval=1d"


def fetch(ticker: str) -> list[list[str]]:
    req = urllib.request.Request(URL.format(ticker=ticker), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.load(resp)["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    rows: list[list[str]] = []
    for i, ts in enumerate(result["timestamp"]):
        values = [quote[k][i] for k in ("open", "high", "low", "close", "volume")]
        if any(v is None for v in values):
            continue
        day = datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")
        if day >= today:  # today's bar is still forming; keep completed sessions only
            continue
        rows.append([day, *(f"{v:.2f}" for v in values[:4]), str(int(values[4]))])
    return rows


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for ticker in TICKERS:
        rows = fetch(ticker)
        with (DATA_DIR / f"{ticker}.csv").open("w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "open", "high", "low", "close", "volume"])
            writer.writerows(rows)
        print(f"{ticker}: {len(rows)} rows ({rows[0][0]} .. {rows[-1][0]})")


if __name__ == "__main__":
    main()

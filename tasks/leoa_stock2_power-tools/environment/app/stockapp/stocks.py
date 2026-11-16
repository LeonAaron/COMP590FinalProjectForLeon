"""Price data access. Prices are read from bundled CSV snapshots in ``data/``."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

TICKERS: dict[str, str] = {
    "NVDA": "NVIDIA Corporation",
    "MSFT": "Microsoft Corporation",
    "AAPL": "Apple Inc.",
    "GOOGL": "Alphabet Inc. (Google)",
    "META": "Meta Platforms, Inc.",
}


@dataclass(frozen=True)
class PriceBar:
    date: str  # ISO format, YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: int

    def to_dict(self) -> dict[str, str | float | int]:
        return asdict(self)


class UnknownTickerError(KeyError):
    """Raised when a ticker is not one of the supported ``TICKERS``."""


def normalize_ticker(ticker: str) -> str:
    symbol = ticker.strip().upper()
    if symbol not in TICKERS:
        raise UnknownTickerError(ticker)
    return symbol


@lru_cache(maxsize=None)
def load_prices(ticker: str) -> tuple[PriceBar, ...]:
    """Return daily bars for ``ticker``, oldest first."""
    symbol = normalize_ticker(ticker)
    with (DATA_DIR / f"{symbol}.csv").open(newline="") as f:
        bars = [
            PriceBar(
                date=row["date"],
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=int(row["volume"]),
            )
            for row in csv.DictReader(f)
        ]
    return tuple(sorted(bars, key=lambda b: b.date))


def latest_bar(ticker: str) -> PriceBar:
    return load_prices(ticker)[-1]

"""Tiny helpers the reference solutions use to patch the app in place."""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

APP = Path(os.environ.get("APP_DIR", "/app"))


def _clean(text: str) -> str:
    return textwrap.dedent(text).strip("\n") + "\n"


def append(rel: str, text: str) -> None:
    path = APP / rel
    path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + "\n\n\n" + _clean(text), encoding="utf-8")


def write(rel: str, text: str) -> None:
    path = APP / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_clean(text), encoding="utf-8")


def replace(rel: str, old: str, new: str) -> None:
    path = APP / rel
    source = path.read_text(encoding="utf-8")
    if source.count(old) != 1:
        raise SystemExit(f"anchor not found exactly once in {rel}: {old!r}")
    path.write_text(source.replace(old, new), encoding="utf-8")


def insert_before(rel: str, anchor: str, text: str) -> None:
    replace(rel, anchor, text + anchor)


def insert_after(rel: str, anchor: str, text: str) -> None:
    replace(rel, anchor, anchor + text)


# Stable anchors in the baseline template.
TEMPLATE = "stockapp/templates/index.html"
DISCLAIMER = '      <p class="disclaimer">'
LATEST_CLOSE = '<strong id="latest-close">${{ "%.2f"|format(latest.close) }}</strong>'
LEGEND = '          <div id="ohlc-legend"'
INDEX_CONTEXT = "        symbol_list={t: latest_bar(t) for t in TICKERS},\n"

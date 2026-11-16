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


NO_STORE_MARKER = "# convention: Cache-Control no-store on /api/ responses"


def no_store() -> None:
    """Add (once) an after-request hook that marks successful /api/ responses no-store."""
    if NO_STORE_MARKER in (APP / "stockapp/routes.py").read_text(encoding="utf-8"):
        return
    append(
        "stockapp/routes.py",
        f"""
        {NO_STORE_MARKER}
        @bp.after_app_request
        def _api_no_store(response):  # noqa: ANN001, ANN202
            if request.path.startswith("/api/") and response.status_code < 400:
                response.headers["Cache-Control"] = "no-store"
            return response
        """,
    )

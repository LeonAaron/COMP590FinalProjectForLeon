"""HTTP routes: one HTML page plus a small JSON API the page's chart reads from."""

from __future__ import annotations

from flask import Blueprint, abort, jsonify, render_template, request
from flask.typing import ResponseReturnValue

from stockapp.stocks import TICKERS, UnknownTickerError, latest_bar, load_prices, normalize_ticker

bp = Blueprint("stocks", __name__)

DEFAULT_TICKER = "NVDA"


@bp.get("/")
def index() -> ResponseReturnValue:
    try:
        selected = normalize_ticker(request.args.get("ticker", DEFAULT_TICKER))
    except UnknownTickerError:
        selected = DEFAULT_TICKER
    return render_template(
        "index.html",
        tickers=TICKERS,
        selected=selected,
        latest=latest_bar(selected),
        symbol_list={t: latest_bar(t) for t in TICKERS},
    )


@bp.get("/api/stocks")
def list_stocks() -> ResponseReturnValue:
    return jsonify([{"ticker": t, "name": name} for t, name in TICKERS.items()])


@bp.get("/api/stocks/<ticker>")
def stock_prices(ticker: str) -> ResponseReturnValue:
    try:
        symbol = normalize_ticker(ticker)
    except UnknownTickerError:
        abort(404, description=f"Unknown ticker: {ticker}")
    return jsonify(
        {
            "ticker": symbol,
            "name": TICKERS[symbol],
            "prices": [bar.to_dict() for bar in load_prices(symbol)],
        }
    )


@bp.app_errorhandler(404)
def not_found(err: Exception) -> ResponseReturnValue:
    if request.path.startswith("/api/"):
        return jsonify({"error": getattr(err, "description", "Not found")}), 404
    return "Not found", 404

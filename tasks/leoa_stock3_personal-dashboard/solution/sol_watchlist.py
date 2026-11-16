from patchlib import DISCLAIMER, INDEX_CONTEXT, TEMPLATE, append, insert_before, write

write(
    "stockapp/watchlist.py",
    '''
    """A watchlist of tickers persisted as a JSON array at $WATCHLIST_PATH."""

    from __future__ import annotations

    import json
    import os
    from pathlib import Path

    from stockapp.stocks import DATA_DIR, normalize_ticker


    def _path() -> Path:
        return Path(os.environ.get("WATCHLIST_PATH", str(DATA_DIR / "watchlist.json")))


    def load_watchlist() -> list[str]:
        path = _path()
        if not path.is_file():
            return []
        return list(json.loads(path.read_text()))


    def _save(tickers: list[str]) -> list[str]:
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(tickers))
        return tickers


    def add_to_watchlist(ticker: str) -> list[str]:
        symbol = normalize_ticker(ticker)
        tickers = load_watchlist()
        if symbol not in tickers:
            tickers.append(symbol)
            _save(tickers)
        return tickers


    def remove_from_watchlist(ticker: str) -> list[str]:
        symbol = ticker.strip().upper()
        tickers = load_watchlist()
        if symbol not in tickers:
            raise KeyError(symbol)
        tickers.remove(symbol)
        return _save(tickers)
    ''',
)

insert_before(
    "stockapp/routes.py",
    INDEX_CONTEXT,
    "        watchlist=[(t, latest_bar(t)) for t in load_watchlist()],\n",
)
append(
    "stockapp/routes.py",
    '''
    from stockapp.watchlist import add_to_watchlist, load_watchlist, remove_from_watchlist  # noqa: E402


    @bp.get("/api/watchlist")
    def get_watchlist() -> ResponseReturnValue:
        return jsonify({"tickers": load_watchlist()})


    @bp.post("/api/watchlist")
    def post_watchlist() -> ResponseReturnValue:
        body = request.get_json(silent=True)
        ticker = body.get("ticker") if isinstance(body, dict) else None
        if not isinstance(ticker, str):
            return jsonify({"error": "body must be a JSON object with a string 'ticker'"}), 400
        before = load_watchlist()
        try:
            tickers = add_to_watchlist(ticker)
        except UnknownTickerError:
            return jsonify({"error": f"Unknown ticker: {ticker}"}), 400
        return jsonify({"tickers": tickers}), (200 if tickers == before else 201)


    @bp.delete("/api/watchlist/<ticker>")
    def delete_watchlist(ticker: str) -> ResponseReturnValue:
        try:
            return jsonify({"tickers": remove_from_watchlist(ticker)})
        except KeyError:
            return jsonify({"error": f"{ticker} is not in the watchlist"}), 404
    ''',
)

insert_before(
    TEMPLATE,
    DISCLAIMER,
    """      <section id="watchlist" class="panel" aria-label="Your watchlist">
        <div class="panel-head"><h3 class="panel-title">Watchlist</h3></div>
        {% if watchlist %}
        <ul class="watchlist-items">
          {% for t, bar in watchlist %}
          <li class="watchlist-item" data-ticker="{{ t }}"><a href="/?ticker={{ t }}">{{ t }}</a> <span>${{ "%.2f"|format(bar.close) }}</span></li>
          {% endfor %}
        </ul>
        {% else %}
        <p class="empty">Your watchlist is empty</p>
        {% endif %}
      </section>

""",
)

from patchlib import no_store  # noqa: E402

no_store()

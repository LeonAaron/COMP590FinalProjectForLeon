from patchlib import DISCLAIMER, INDEX_CONTEXT, TEMPLATE, append, insert_before

append(
    "stockapp/stocks.py",
    '''
    def top_movers(date: str | None = None, limit: int = 5) -> list[dict[str, str | float]]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= len(TICKERS):
            raise ValueError("limit must be an int from 1 to 5")
        rows = []
        for symbol, name in TICKERS.items():
            bars = load_prices(symbol)
            dates = [b.date for b in bars]
            index = len(bars) - 1 if date is None else (dates.index(date) if date in dates else -1)
            if index <= 0:
                raise ValueError(f"no change available for {date}")
            close, prev = bars[index].close, bars[index - 1].close
            rows.append({"ticker": symbol, "name": name, "close": close,
                         "change_pct": round((close - prev) / prev * 100, 2)})
        rows.sort(key=lambda r: (-r["change_pct"], r["ticker"]))
        return rows[:limit]
    ''',
)

insert_before("stockapp/routes.py", INDEX_CONTEXT, "        movers=top_movers(),\n")
append(
    "stockapp/routes.py",
    '''
    from stockapp.stocks import top_movers  # noqa: E402


    @bp.get("/api/movers")
    def api_movers() -> ResponseReturnValue:
        date = request.args.get("date")
        try:
            limit = int(request.args.get("limit", "5"))
            movers = top_movers(date, limit)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"date": date or latest_bar("NVDA").date, "movers": movers})
    ''',
)

insert_before(
    TEMPLATE,
    DISCLAIMER,
    """      <section id="movers" class="panel" aria-label="Top movers">
        <div class="panel-head"><h3 class="panel-title">Top Movers</h3></div>
        <ul>
          {% for m in movers %}
          <li class="mover {{ 'up' if m.change_pct >= 0 else 'down' }}" data-ticker="{{ m.ticker }}">{{ m.ticker }} <span>{{ "%+.2f"|format(m.change_pct) }}%</span></li>
          {% endfor %}
        </ul>
      </section>

""",
)

from patchlib import no_store  # noqa: E402

no_store()

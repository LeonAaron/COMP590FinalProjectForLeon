from patchlib import INDEX_CONTEXT, LATEST_CLOSE, TEMPLATE, append, insert_after, insert_before, replace

append(
    "stockapp/stocks.py",
    '''
    def daily_change(ticker: str, date: str | None = None) -> dict[str, str | float]:
        """Change versus the previous trading day's close."""
        bars = load_prices(ticker)
        if date is None:
            index = len(bars) - 1
        else:
            dates = [b.date for b in bars]
            if date not in dates:
                raise ValueError(f"{date} is not a trading day in the data")
            index = dates.index(date)
        if index == 0:
            raise ValueError("no previous close for the first day")
        close, prev = bars[index].close, bars[index - 1].close
        return {
            "date": bars[index].date,
            "close": close,
            "prev_close": prev,
            "change": round(close - prev, 2),
            "change_pct": round((close - prev) / prev * 100, 2),
        }
    ''',
)

replace(
    "stockapp/routes.py",
    '            "prices": [bar.to_dict() for bar in load_prices(symbol)],\n',
    '            "prices": [bar.to_dict() for bar in load_prices(symbol)],\n'
    '            "latest_change": daily_change(symbol),\n',
)
insert_before("stockapp/routes.py", INDEX_CONTEXT, "        change=daily_change(selected),\n")
append(
    "stockapp/routes.py",
    '''
    from stockapp.stocks import daily_change  # noqa: E402


    @bp.get("/api/stocks/<ticker>/change")
    def stock_change(ticker: str) -> ResponseReturnValue:
        try:
            symbol = normalize_ticker(ticker)
        except UnknownTickerError:
            abort(404, description=f"Unknown ticker: {ticker}")
        try:
            return jsonify(daily_change(symbol, request.args.get("date")))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    ''',
)

insert_after(
    TEMPLATE,
    LATEST_CLOSE,
    '\n            {% set sign = "+" if change.change >= 0 else "-" %}'
    '\n            <span id="day-change" class="day-change {{ "up" if sign == "+" else "down" }}">'
    '{{ sign }}{{ "%.2f"|format(change.change|abs) }} ({{ sign }}{{ "%.2f"|format(change.change_pct|abs) }}%)</span>',
)
append(
    "stockapp/static/style.css",
    """
    .day-change { display: block; font-weight: 600; font-variant-numeric: tabular-nums; }
    .day-change.up { color: var(--up); }
    .day-change.down { color: var(--down); }
    """,
)

from patchlib import no_store  # noqa: E402

no_store()

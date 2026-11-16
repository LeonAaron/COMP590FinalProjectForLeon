from patchlib import LEGEND, TEMPLATE, append, insert_before, replace

append(
    "stockapp/stocks.py",
    '''
    def _parse_day(value: str) -> str:
        import datetime as _dt
        import re as _re

        if not isinstance(value, str) or not _re.fullmatch(r"\\d{4}-\\d{2}-\\d{2}", value):
            raise ValueError(f"invalid date: {value!r}")
        _dt.date.fromisoformat(value)  # raises ValueError for impossible dates
        return value


    def prices_between(ticker: str, start: str | None = None, end: str | None = None) -> list[PriceBar]:
        lo = _parse_day(start) if start is not None else None
        hi = _parse_day(end) if end is not None else None
        if lo and hi and lo > hi:
            raise ValueError("start is after end")
        return [b for b in load_prices(ticker) if (lo is None or b.date >= lo) and (hi is None or b.date <= hi)]
    ''',
)

replace(
    "stockapp/routes.py",
    '''    return jsonify(
        {
            "ticker": symbol,
            "name": TICKERS[symbol],
            "prices": [bar.to_dict() for bar in load_prices(symbol)],
        }
    )''',
    '''    try:
        bars = _filtered_bars(symbol)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(
        {
            "ticker": symbol,
            "name": TICKERS[symbol],
            "prices": [bar.to_dict() for bar in bars],
        }
    )''',
)
append(
    "stockapp/routes.py",
    '''
    import datetime as _dt  # noqa: E402

    from stockapp.stocks import prices_between  # noqa: E402

    RANGE_DAYS = {"1M": 30, "3M": 91, "6M": 182, "1Y": 365}


    def _filtered_bars(symbol: str) -> list:
        start, end, rng = request.args.get("start"), request.args.get("end"), request.args.get("range")
        if rng is not None:
            if start is not None or end is not None:
                raise ValueError("range cannot be combined with start/end")
            if rng not in RANGE_DAYS:
                raise ValueError(f"range must be one of {list(RANGE_DAYS)}")
            last = _dt.date.fromisoformat(load_prices(symbol)[-1].date)
            start = (last - _dt.timedelta(days=RANGE_DAYS[rng])).isoformat()
        return prices_between(symbol, start, end)
    ''',
)

insert_before(
    TEMPLATE,
    LEGEND,
    '          <div class="range-buttons">'
    '<button class="range-btn" data-range="1M">1M</button>'
    '<button class="range-btn" data-range="3M">3M</button>'
    '<button class="range-btn" data-range="6M">6M</button>'
    '<button class="range-btn active" data-range="1Y">1Y</button></div>\n',
)

replace(
    "stockapp/static/app.js",
    "  async function render(ticker) {\n    const resp = await fetch(`/api/stocks/${encodeURIComponent(ticker)}`);",
    "  let current = null;\n"
    "  async function render(ticker, range) {\n"
    "    const qs = range ? `?range=${range}` : \"\";\n"
    "    const resp = await fetch(`/api/stocks/${encodeURIComponent(ticker)}${qs}`);",
)
replace(
    "stockapp/static/app.js",
    "    const chart = LightweightCharts.createChart(container, {",
    "    if (current) current.remove();\n    const chart = LightweightCharts.createChart(container, {",
)
replace(
    "stockapp/static/app.js",
    "    chart.timeScale().fitContent();\n",
    "    chart.timeScale().fitContent();\n    current = chart;\n",
)
replace(
    "stockapp/static/app.js",
    "  render(container.dataset.ticker);\n",
    """  document.querySelectorAll(".range-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".range-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      render(container.dataset.ticker, btn.dataset.range);
    });
  });
  render(container.dataset.ticker);
""",
)

from patchlib import LEGEND, TEMPLATE, append, insert_before, replace

append(
    "stockapp/stocks.py",
    '''
    def moving_average(ticker: str, window: int) -> list[dict[str, str | float]]:
        """Simple moving average of closes; one entry per day with a full window."""
        bars = load_prices(ticker)
        if isinstance(window, bool) or not isinstance(window, int) or not 2 <= window <= len(bars):
            raise ValueError(f"window must be an int between 2 and {len(bars)}")
        closes = [b.close for b in bars]
        return [
            {"date": bars[i].date, "value": round(sum(closes[i - window + 1 : i + 1]) / window, 2)}
            for i in range(window - 1, len(bars))
        ]
    ''',
)

append(
    "stockapp/routes.py",
    '''
    from stockapp.stocks import moving_average  # noqa: E402


    @bp.get("/api/stocks/<ticker>/sma")
    def stock_sma(ticker: str) -> ResponseReturnValue:
        try:
            symbol = normalize_ticker(ticker)
        except UnknownTickerError:
            abort(404, description=f"Unknown ticker: {ticker}")
        raw = request.args.get("window", "20")
        try:
            window = int(raw)
            values = moving_average(symbol, window)
        except ValueError:
            return jsonify({"error": f"invalid window: {raw!r}"}), 400
        return jsonify({"ticker": symbol, "window": window, "values": values})
    ''',
)

insert_before(
    TEMPLATE,
    LEGEND,
    '          <label class="sma-control"><input type="checkbox" id="sma-toggle"> '
    '</label><label for="sma-toggle">20-day SMA</label>\n',
)

replace(
    "stockapp/static/app.js",
    "    chart.timeScale().fitContent();\n",
    """    chart.timeScale().fitContent();

    // Optional 20-day SMA overlay.
    const toggle = document.getElementById("sma-toggle");
    let sma = null;
    toggle.addEventListener("change", async () => {
      if (sma) { chart.removeSeries(sma); sma = null; }
      if (!toggle.checked) return;
      const r = await fetch(`/api/stocks/${encodeURIComponent(ticker)}/sma?window=20`);
      if (!r.ok) return;
      const body = await r.json();
      sma = chart.addLineSeries({ color: "#4f46e5", lineWidth: 2, priceLineVisible: false, lastValueVisible: false });
      sma.setData(body.values.map((v) => ({ time: v.date, value: v.value })));
    });
""",
)

from patchlib import no_store  # noqa: E402

no_store()

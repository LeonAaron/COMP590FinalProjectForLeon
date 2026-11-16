from patchlib import TEMPLATE, append, insert_after, write

append(
    "stockapp/stocks.py",
    '''
    def summary_stats(ticker: str) -> dict[str, str | float | int]:
        import math
        import statistics

        symbol = normalize_ticker(ticker)
        bars = load_prices(symbol)
        closes = [b.close for b in bars]
        logs = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        return {
            "ticker": symbol,
            "name": TICKERS[symbol],
            "last_close": closes[-1],
            "high_52w": max(b.high for b in bars),
            "low_52w": min(b.low for b in bars),
            "avg_volume": round(sum(b.volume for b in bars) / len(bars)),
            "return_1y_pct": round((closes[-1] / closes[0] - 1) * 100, 2),
            "volatility_pct": round(statistics.stdev(logs) * math.sqrt(252) * 100, 2),
        }
    ''',
)

append(
    "stockapp/routes.py",
    '''
    from stockapp.stocks import summary_stats  # noqa: E402


    @bp.get("/api/summary")
    def api_summary() -> ResponseReturnValue:
        return jsonify([summary_stats(t) for t in TICKERS])


    @bp.get("/dashboard")
    def dashboard() -> ResponseReturnValue:
        return render_template("dashboard.html", rows=[summary_stats(t) for t in TICKERS])
    ''',
)

write(
    "stockapp/templates/dashboard.html",
    """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Dashboard · Stock Chart Viewer</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
      <header class="topbar"><div class="topbar-inner"><a class="brand" href="/"><span class="brand-mark"></span><span class="brand-name">Stock Chart Viewer</span></a></div></header>
      <div class="layout" style="grid-template-columns: minmax(0, 1fr)">
        <section class="panel" style="padding: 18px; overflow-x: auto">
          <h3 class="panel-title">Market Summary</h3>
          <table id="summary-table">
            <thead><tr><th>Symbol</th><th>Last Close</th><th>52W High</th><th>52W Low</th><th>Avg Volume</th><th>1Y Return</th><th>Volatility</th></tr></thead>
            <tbody>
              {% for r in rows %}
              <tr data-ticker="{{ r.ticker }}"><td>{{ r.ticker }}</td><td>{{ "%.2f"|format(r.last_close) }}</td><td>{{ "%.2f"|format(r.high_52w) }}</td><td>{{ "%.2f"|format(r.low_52w) }}</td><td>{{ "{:,}".format(r.avg_volume) }}</td><td>{{ "%+.2f"|format(r.return_1y_pct) }}%</td><td>{{ "%.2f"|format(r.volatility_pct) }}%</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </section>
      </div>
    </body>
    </html>
    """,
)

insert_after(
    TEMPLATE,
    '      <span class="crumb current">{{ selected }}</span>\n',
    '      <a class="crumb" href="/dashboard" style="margin-left:auto">Dashboard</a>\n',
)

from patchlib import TEMPLATE, append, insert_after, write

append(
    "stockapp/stocks.py",
    '''
    def compare(tickers: list[str]) -> dict:
        symbols = [normalize_ticker(t) for t in tickers]
        if not 2 <= len(symbols) <= 5:
            raise ValueError("compare needs 2 to 5 tickers")
        if len(set(symbols)) != len(symbols):
            raise ValueError("duplicate ticker")
        closes = {s: {b.date: b.close for b in load_prices(s)} for s in symbols}
        common = sorted(set.intersection(*(set(c) for c in closes.values())))
        return {
            "tickers": symbols,
            "dates": common,
            "series": {s: [round(closes[s][d] / closes[s][common[0]] * 100, 2) for d in common] for s in symbols},
        }
    ''',
)

append(
    "stockapp/routes.py",
    '''
    from stockapp.stocks import compare  # noqa: E402


    def _split_tickers(raw: str | None) -> list[str]:
        return [part.strip() for part in (raw or "").split(",") if part.strip()]


    @bp.get("/api/compare")
    def api_compare() -> ResponseReturnValue:
        try:
            return jsonify(compare(_split_tickers(request.args.get("tickers"))))
        except (ValueError, UnknownTickerError) as exc:
            return jsonify({"error": str(exc)}), 400


    @bp.get("/compare")
    def compare_page() -> ResponseReturnValue:
        try:
            result = compare(_split_tickers(request.args.get("tickers")))
        except (ValueError, UnknownTickerError):
            result = compare(list(TICKERS))
        return render_template("compare.html", result=result)
    ''',
)

write(
    "stockapp/templates/compare.html",
    """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Compare · Stock Chart Viewer</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
      <header class="topbar"><div class="topbar-inner"><a class="brand" href="/"><span class="brand-mark"></span><span class="brand-name">Stock Chart Viewer</span></a></div></header>
      <div class="layout" style="grid-template-columns: minmax(0, 1fr)">
        <section class="panel" style="padding: 18px">
          <h3 class="panel-title">Relative performance (start = 100)</h3>
          <div id="compare-chart" data-tickers="{{ result.tickers|join(',') }}" style="height: 400px"></div>
          <table id="compare-table"><caption>Final rebased value per stock</caption>
            <thead><tr><th>Symbol</th><th>Last value</th></tr></thead>
            <tbody>
              {% for t in result.tickers %}
              <tr data-ticker="{{ t }}"><td>{{ t }}</td><td>{{ "%.2f"|format(result.series[t][-1]) }}</td></tr>
              {% endfor %}
            </tbody>
          </table>
        </section>
      </div>
      <script src="{{ url_for('static', filename='vendor/lightweight-charts-4.2.0.js') }}"></script>
      <script>
        (async function () {
          const el = document.getElementById("compare-chart");
          const data = await (await fetch(`/api/compare?tickers=${el.dataset.tickers}`)).json();
          const chart = LightweightCharts.createChart(el, { autoSize: true });
          const colors = ["#4f46e5", "#16a34a", "#dc2626", "#f59e0b", "#0ea5e9"];
          data.tickers.forEach((t, i) => {
            const s = chart.addLineSeries({ color: colors[i], lineWidth: 2, title: t });
            s.setData(data.dates.map((d, j) => ({ time: d, value: data.series[t][j] })));
          });
          chart.timeScale().fitContent();
        })();
      </script>
    </body>
    </html>
    """,
)

insert_after(
    TEMPLATE,
    '      <span class="crumb current">{{ selected }}</span>\n',
    '      <a class="crumb" href="/compare" style="margin-left:auto">Compare</a>\n',
)

from patchlib import no_store  # noqa: E402

no_store()

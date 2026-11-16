from patchlib import TEMPLATE, append, insert_after, write

write(
    "stockapp/report.py",
    '''
    """Markdown analysis report for one stock."""

    from __future__ import annotations

    import math
    import statistics

    from stockapp.stocks import TICKERS, load_prices, normalize_ticker


    def generate_report(ticker: str) -> str:
        symbol = normalize_ticker(ticker)
        bars = load_prices(symbol)
        closes = [b.close for b in bars]
        logs = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        sma50 = sum(closes[-50:]) / 50
        last = closes[-1]
        trend = "Bullish" if last > sma50 else "Bearish" if last < sma50 else "Neutral"
        return (
            f"# {TICKERS[symbol]} ({symbol}) Analysis Report\\n\\n"
            "## Price Summary\\n"
            f"- Last close: ${last:.2f} (as of {bars[-1].date})\\n"
            f"- 52-week high: ${max(b.high for b in bars):.2f}\\n"
            f"- 52-week low: ${min(b.low for b in bars):.2f}\\n\\n"
            "## Performance\\n"
            f"- 1-year return: {(last / closes[0] - 1) * 100:+.2f}%\\n"
            f"- 1-month return: {(last / closes[-22] - 1) * 100:+.2f}%\\n\\n"
            "## Volatility\\n"
            f"- Annualized volatility: {statistics.stdev(logs) * math.sqrt(252) * 100:.2f}%\\n\\n"
            "## Trend\\n"
            f"- 50-day SMA: ${sma50:.2f}\\n"
            f"- Trend: {trend}\\n"
        )


    def report_blocks(markdown: str) -> list[tuple[str, str | list[str]]]:
        """Parse the report into (kind, content) blocks for HTML rendering."""
        blocks: list[tuple[str, str | list[str]]] = []
        for line in markdown.splitlines():
            if line.startswith("# "):
                blocks.append(("h1", line[2:]))
            elif line.startswith("## "):
                blocks.append(("h2", line[3:]))
            elif line.startswith("- "):
                if not blocks or blocks[-1][0] != "ul":
                    blocks.append(("ul", []))
                items = blocks[-1][1]
                assert isinstance(items, list)
                items.append(line[2:])
        return blocks
    ''',
)

append(
    "stockapp/routes.py",
    '''
    from flask import Response  # noqa: E402

    from stockapp.report import generate_report, report_blocks  # noqa: E402


    @bp.get("/api/stocks/<ticker>/report.md")
    def report_markdown(ticker: str) -> ResponseReturnValue:
        try:
            text = generate_report(ticker)
        except UnknownTickerError:
            abort(404, description=f"Unknown ticker: {ticker}")
        return Response(text, mimetype="text/markdown")


    @bp.get("/report/<ticker>")
    def report_page(ticker: str) -> ResponseReturnValue:
        try:
            symbol = normalize_ticker(ticker)
        except UnknownTickerError:
            abort(404)
        return render_template("report.html", ticker=symbol, blocks=report_blocks(generate_report(symbol)))
    ''',
)

write(
    "stockapp/templates/report.html",
    """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{{ ticker }} Analysis Report · Stock Chart Viewer</title>
      <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    </head>
    <body>
      <header class="topbar"><div class="topbar-inner"><a class="brand" href="/?ticker={{ ticker }}"><span class="brand-mark"></span><span class="brand-name">Stock Chart Viewer</span></a></div></header>
      <div class="layout" style="grid-template-columns: minmax(0, 1fr)">
        <article id="report" class="panel" style="padding: 18px 24px">
          {% for kind, content in blocks %}
          {% if kind == "ul" %}<ul>{% for item in content %}<li>{{ item }}</li>{% endfor %}</ul>
          {% else %}<{{ kind }}>{{ content }}</{{ kind }}>{% endif %}
          {% endfor %}
        </article>
      </div>
    </body>
    </html>
    """,
)

insert_after(
    TEMPLATE,
    '            <p class="exchange">NASDAQ · USD</p>\n',
    '            <a id="report-link" href="/report/{{ selected }}">Analysis report</a>\n',
)

from patchlib import no_store  # noqa: E402

no_store()

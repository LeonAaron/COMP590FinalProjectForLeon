from patchlib import LEGEND, TEMPLATE, append, insert_before

append(
    "stockapp/routes.py",
    '''
    import csv as _csv  # noqa: E402
    import io as _io  # noqa: E402

    from flask import Response  # noqa: E402


    @bp.get("/api/stocks/<ticker>/export.csv")
    def export_csv(ticker: str) -> ResponseReturnValue:
        try:
            symbol = normalize_ticker(ticker)
        except UnknownTickerError:
            abort(404, description=f"Unknown ticker: {ticker}")
        order = request.args.get("order", "asc")
        if order not in ("asc", "desc"):
            return jsonify({"error": "order must be 'asc' or 'desc'"}), 400
        bars = load_prices(symbol)
        rows = []
        for i, b in enumerate(bars):
            pct = "" if i == 0 else f"{round((b.close - bars[i - 1].close) / bars[i - 1].close * 100, 2):.2f}"
            rows.append([b.date, f"{b.open:.2f}", f"{b.high:.2f}", f"{b.low:.2f}", f"{b.close:.2f}", b.volume, pct])
        if order == "desc":
            rows.reverse()
        buf = _io.StringIO()
        writer = _csv.writer(buf)
        writer.writerow(["date", "open", "high", "low", "close", "volume", "change_pct"])
        writer.writerows(rows)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{symbol}_prices.csv"'},
        )
    ''',
)

insert_before(
    TEMPLATE,
    LEGEND,
    '          <a id="export-link" href="/api/stocks/{{ selected }}/export.csv" download>Export CSV</a>\n',
)

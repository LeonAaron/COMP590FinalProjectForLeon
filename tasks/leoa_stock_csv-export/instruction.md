You are working on a small Flask web app in `/app` called **Stock Chart Viewer**.
It shows one year of daily prices for five stocks (NVDA, MSFT, AAPL, GOOGL, META)
read from bundled CSV files in `stockapp/data/`.

- `stockapp/stocks.py` is the data layer (`TICKERS`, `PriceBar`, `load_prices`, `latest_bar`, `normalize_ticker`, `UnknownTickerError`).
- `stockapp/routes.py` holds the HTTP routes (a Flask blueprint registered by `create_app()` in `stockapp/__init__.py`).
- `stockapp/templates/index.html` is the main page; `stockapp/static/` holds its JavaScript and CSS.
- `tests/` holds the existing tests. Run them from `/app` with `python -m pytest`. They must keep passing.

Do not change the CSV data files or the existing behaviour described above. Use only
the Python standard library and Flask (no new dependencies, no network access at runtime).

Implement the feature below. Your work will be checked by automated tests that use
exactly the names, routes, JSON fields and HTML element ids given in this specification.

---

# Feature: CSV export

Let users download a stock's price history as a CSV file.

## API (`stockapp/routes.py`, plus any helpers you need)

`GET /api/stocks/<ticker>/export.csv`

- Response content type is `text/csv`, and the response has a `Content-Disposition` header that makes the browser
  download it as an attachment named `<TICKER>_prices.csv` (normalized symbol, e.g. `NVDA_prices.csv`).
- The body is CSV with this header row and one row per trading day:
  `date,open,high,low,close,volume,change_pct`
  - `open`, `high`, `low`, `close` are written with exactly 2 decimals (e.g. `162.80`).
  - `volume` is written as a whole number.
  - `change_pct` is the percentage change of that day's close versus the **previous trading day's** close,
    `round((close - prev_close) / prev_close * 100, 2)`, written with exactly 2 decimals. It is an empty field for the first
    (oldest) day, which has no previous close.
- Optional query parameter `order`: `asc` (default, oldest first) or `desc` (newest first). In `desc` order each row's
  `change_pct` is still relative to the previous **chronological** day, so the empty `change_pct` is on the last row.
  Any other value: status **400** with a JSON `"error"` key.
- Unknown ticker: status 404 with a JSON `"error"` key.

## UI

Add a download link to the chart panel of the main page:
`<a id="export-link" href="/api/stocks/<SELECTED TICKER>/export.csv" download>Export CSV</a>`.

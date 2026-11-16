You are working on a small Flask web app in `/app` called **Stock Chart Viewer**.
It shows one year of daily prices for five stocks (NVDA, MSFT, AAPL, GOOGL, META)
read from bundled CSV files in `stockapp/data/`.

- `stockapp/stocks.py` is the data layer (`TICKERS`, `PriceBar`, `load_prices`, `latest_bar`, `normalize_ticker`, `UnknownTickerError`).
- `stockapp/routes.py` holds the HTTP routes (a Flask blueprint registered by `create_app()` in `stockapp/__init__.py`).
- `stockapp/templates/index.html` is the main page; `stockapp/static/` holds its JavaScript and CSS.
- `tests/` holds the existing tests. Run them from `/app` with `python -m pytest`. They must keep passing.

Do not change the CSV data files or break existing behaviour. Use only the Python
standard library and Flask (no new dependencies, no network access at runtime).

This release adds several features, described below. Your work will be checked by automated tests
that exercise the names, routes, JSON fields and HTML element ids given in the descriptions, and
that expect the codebase conventions below to hold everywhere.

## Codebase conventions (apply to every feature)

- **Tickers** are case-insensitive and ignore surrounding whitespace wherever a user supplies one (URL path,
  query string, JSON body, Python argument). Output always uses the upper-case symbol.
- **Data-layer functions** raise `UnknownTickerError` for unknown tickers and `ValueError` for any other invalid
  argument (wrong type, out of range, a date that is not usable, ...). `bool` is never accepted where a number is expected.
- **JSON API errors** return a JSON object with an `"error"` key. Use status **404** when the resource named in the
  URL path does not exist (unknown ticker in the path, unknown id), and **400** for any other invalid input (bad or missing
  query parameters, malformed or wrongly typed JSON bodies, unknown tickers given in a query string or body).
- **Dates** are strings in exactly `YYYY-MM-DD` form and must be real calendar dates. "The previous close" always means the
  close of the previous trading day present in the data; the oldest day has no previous close.
- **Numbers**: computed prices and percentages are rounded to 2 decimals (round the final value, not intermediate
  steps). A percentage change is `(new - old) / old * 100`. In HTML, prices and percentages are shown with exactly 2
  decimals, and signed changes always carry an explicit sign (`+1.20`, `-0.35%`, zero shown as `+0.00`).
- **Annualized volatility** is the sample standard deviation of daily log returns `ln(close_t / close_{t-1})`, times
  `sqrt(252)`, times 100.
- New pages reuse the main page's header and stylesheet so they look like part of the same app.

---

## Feature: market summary dashboard

Users want one page that summarizes every stock.

- Data layer: `summary_stats(ticker)` returns `ticker`, `name`, `last_close`, `high_52w` (highest high), `low_52w`
  (lowest low), `avg_volume` (mean daily volume as a whole number), `return_1y_pct` (first close to last close) and
  `volatility_pct` (annualized), all over the full data set.
- API: `GET /api/summary` lists `summary_stats` for every ticker in `TICKERS` order.
- UI: a `/dashboard` page with `<table id="summary-table">`, columns `Symbol`, `Last Close`, `52W High`, `52W Low`,
  `Avg Volume`, `1Y Return`, `Volatility`, and one `<tr data-ticker="...">` per stock. Volumes use thousands separators;
  the return is signed; the volatility is a plain percentage. The main page links to it (`href="/dashboard"`).

## Feature: compare stocks

Users want to compare the relative performance of 2 to 5 different stocks.

- Data layer: `compare(tickers)` returns `{"tickers", "dates", "series"}`: the symbols in the order given, the dates
  every one of them has, and per ticker its closes rebased so its first common date is exactly 100.
- API: `GET /api/compare?tickers=NVDA,msft` (comma-separated; blanks around or between commas are ignored).
- UI: a `/compare` page (optional `tickers` parameter; it falls back to all five stocks when the parameter is missing
  or unusable) with `<div id="compare-chart" data-tickers="NVDA,MSFT">` drawn by JavaScript, and a
  `<table id="compare-table">` with one `<tr data-ticker="...">` per stock showing its symbol and final rebased value.
  The main page links to it (an `href` starting with `/compare`).

## Feature: CSV export

Users want to download a stock's history to open in a spreadsheet.

- `GET /api/stocks/<ticker>/export.csv` downloads (as an attachment named `<TICKER>_prices.csv`) a `text/csv` file
  with columns `date,open,high,low,close,volume,change_pct`, one row per trading day. Prices have 2 decimals, volume is
  a whole number, and `change_pct` is the day's change versus the previous close (left empty when there is none).
- Optional `order=asc|desc` (default `asc`, oldest first). Reversing the order must not change what each row's
  `change_pct` means.
- UI: an `<a id="export-link" ... download>` in the chart panel pointing at the selected stock's export.

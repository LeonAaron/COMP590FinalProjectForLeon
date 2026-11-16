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
- **New pages** reuse the main page's header (`<header class="topbar">` containing the `brand` link back to `/`) and
  stylesheet, and their `<title>` is `<page name> · Stock Chart Viewer` (the page name is given with each feature).
- **New API endpoints** (every new route under `/api/`) send the header `Cache-Control: no-store` on successful
  responses, because prices and user data must never be served stale.
- **Server rendering**: new panels, tables and lists show their content in the HTML the server returns (JavaScript may
  enhance the page, but the content must not depend on it).
- **Accessibility**: every new `<table>` has a `<caption>`, and every new panel `<section>` added to a page has an
  `aria-label` describing it.

---

## Feature: market summary dashboard

Users want one page that summarizes every stock.

- Data layer: `summary_stats(ticker)` returns `ticker`, `name`, `last_close`, `high_52w` (highest high), `low_52w`
  (lowest low), `avg_volume` (mean daily volume as a whole number), `return_1y_pct` (first close to last close) and
  `volatility_pct` (annualized), all over the full data set.
- API: `GET /api/summary` lists `summary_stats` for every ticker in `TICKERS` order.
- UI: a `/dashboard` page (page name: `Dashboard`) with `<table id="summary-table">`, columns `Symbol`, `Last Close`, `52W High`, `52W Low`,
  `Avg Volume`, `1Y Return`, `Volatility`, and one `<tr data-ticker="...">` per stock. Volumes use thousands separators;
  the return is signed; the volatility is a plain percentage. The main page links to it (`href="/dashboard"`).

## Feature: analysis report

Users want a short written report on a stock that they can read in the app or download as Markdown.

- `generate_report(ticker)` in a new module `stockapp/report.py` returns this Markdown (blocks separated by one blank
  line, ending with a newline):

  ```
  # {company name} ({TICKER}) Analysis Report

  ## Price Summary
  - Last close: ${close} (as of {date})
  - 52-week high: ${highest high}
  - 52-week low: ${lowest low}

  ## Performance
  - 1-year return: {first close to last close}%
  - 1-month return: {close 21 trading days before the last one, to the last close}%

  ## Volatility
  - Annualized volatility: {volatility}%

  ## Trend
  - 50-day SMA: ${mean of the last 50 closes}
  - Trend: {Bullish | Bearish | Neutral}
  ```

  The trend is Bullish when the last close is above the 50-day SMA, Bearish when below, Neutral when equal.
  Money is written like `$1234.50`; returns are signed.
- `GET /api/stocks/<ticker>/report.md` serves the Markdown as `text/markdown`.
- `GET /report/<ticker>` (page name: `<TICKER> Analysis Report`, e.g. `NVDA Analysis Report`) renders it as HTML inside `<article id="report">` (title as `<h1>`, sections as `<h2>`, bullets
  as `<li>`), and the main page links to the selected stock's report with `<a id="report-link">`.

## Feature: CSV export

Users want to download a stock's history to open in a spreadsheet.

- `GET /api/stocks/<ticker>/export.csv` downloads (as an attachment named `<TICKER>_prices.csv`) a `text/csv` file
  with columns `date,open,high,low,close,volume,change_pct`, one row per trading day. Prices have 2 decimals, volume is
  a whole number, and `change_pct` is the day's change versus the previous close (left empty when there is none).
- Optional `order=asc|desc` (default `asc`, oldest first). Reversing the order must not change what each row's
  `change_pct` means.
- UI: an `<a id="export-link" ... download>` in the chart panel pointing at the selected stock's export.

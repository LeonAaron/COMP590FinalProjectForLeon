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

# Feature: market summary dashboard

Add a dashboard page that summarizes every stock in one table.

## Data layer (`stockapp/stocks.py`)

Add `summary_stats(ticker: str) -> dict` returning exactly these keys, computed over **all** bars in the data:

| key | definition |
|---|---|
| `ticker` | normalized symbol, e.g. `"NVDA"` |
| `name` | company name from `TICKERS` |
| `last_close` | close of the latest day |
| `high_52w` | highest `high` of any day |
| `low_52w` | lowest `low` of any day |
| `avg_volume` | mean daily volume, rounded to the nearest whole number, as an `int` |
| `return_1y_pct` | `(last close / first close - 1) * 100`, rounded to 2 decimals |
| `volatility_pct` | annualized volatility: the **sample** standard deviation of daily log returns `ln(close_t / close_{t-1})`, times `sqrt(252)`, times 100, rounded to 2 decimals |

Ticker matching is case-insensitive; unknown tickers raise `UnknownTickerError`.

## API (`stockapp/routes.py`)

`GET /api/summary` returns a JSON list with one `summary_stats` dict per ticker, in the same order as `TICKERS`.

## UI

- New page `GET /dashboard` (HTML, status 200) with a table `<table id="summary-table">`.
  - The header row has these column headings, in this order:
    `Symbol`, `Last Close`, `52W High`, `52W Low`, `Avg Volume`, `1Y Return`, `Volatility`.
  - One body row per ticker (in `TICKERS` order) as `<tr data-ticker="<TICKER>">`. Cells show, in the column
    order above: the symbol; prices with 2 decimals (e.g. `162.85`); the average volume with thousands
    separators (e.g. `12,345,678`); and both percentages with 2 decimals followed by `%`, the return with an
    explicit sign (e.g. `+12.34%` or `-5.00%`), the volatility without one (e.g. `45.67%`).
- Reuse the main page's header and styling so the dashboard looks like part of the same app.
- The main page (`/`) has a link to the dashboard: an `<a>` element with `href="/dashboard"`.

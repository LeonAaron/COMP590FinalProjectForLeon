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

# Feature: stock analysis report

Generate a short analysis report for a stock, available as Markdown and as a web page.

## Report generator (new module `stockapp/report.py`)

Add `generate_report(ticker: str) -> str` that returns Markdown with **exactly** this structure (one blank line
between blocks, a trailing newline at the end, no other text):

```
# {name} ({TICKER}) Analysis Report

## Price Summary
- Last close: ${last_close} (as of {last_date})
- 52-week high: ${high}
- 52-week low: ${low}

## Performance
- 1-year return: {return_1y}%
- 1-month return: {return_1m}%

## Volatility
- Annualized volatility: {volatility}%

## Trend
- 50-day SMA: ${sma50}
- Trend: {trend}
```

Definitions (all bars in the data, oldest first):

- `name` comes from `TICKERS`; `TICKER` is the normalized symbol. Ticker matching is case-insensitive; unknown tickers raise `UnknownTickerError`.
- `last_close`/`last_date`: the latest day. `high`: highest `high` of any day. `low`: lowest `low` of any day.
- `return_1y`: `(last close / first close - 1) * 100`.
- `return_1m`: `(last close / close 21 trading days earlier - 1) * 100`, i.e. compared with the close of the bar 21 positions before the latest (`closes[-22]`).
- `volatility`: sample standard deviation of daily log returns `ln(close_t / close_{t-1})` times `sqrt(252)` times 100.
- `sma50`: mean of the last 50 closes.
- `trend`: `Bullish` if the last close is above the 50-day SMA, `Bearish` if below, `Neutral` if equal (compare unrounded values).

Formatting: every money value uses 2 decimals with no thousands separator (e.g. `$1234.50`); both returns use 2
decimals with an explicit sign (e.g. `+12.34`, `-0.50`); volatility uses 2 decimals without a sign.

## API and UI (`stockapp/routes.py`, templates)

- `GET /api/stocks/<ticker>/report.md` returns the Markdown with a `text/markdown` content type. Unknown ticker: status 404 with a JSON `"error"` key.
- `GET /report/<ticker>` returns an HTML page (status 200) that renders the report inside `<article id="report">`:
  the title as an `<h1>`, each section heading as an `<h2>`, and each bullet as an `<li>` (in `<ul>` lists). Text must
  be HTML-escaped. Unknown ticker: status 404.
- The main page has a link `<a id="report-link" href="/report/<SELECTED TICKER>">` for the currently selected stock.

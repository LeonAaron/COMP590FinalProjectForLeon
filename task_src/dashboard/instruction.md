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

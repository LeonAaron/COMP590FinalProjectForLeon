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

# Feature: daily price change

Show how much a stock moved on a given trading day compared with the previous close.

## Data layer (`stockapp/stocks.py`)

Add `daily_change(ticker: str, date: str | None = None) -> dict`.

- `date` is an ISO date (`YYYY-MM-DD`). When it is `None`, use the latest date in the data.
- Return a dict with exactly these keys:
  - `"date"`: the date used
  - `"close"`: that day's close
  - `"prev_close"`: the close of the previous trading day in the data
  - `"change"`: `close - prev_close`, rounded to 2 decimals
  - `"change_pct"`: `(close - prev_close) / prev_close * 100`, rounded to 2 decimals (compute from the unrounded change)
- Ticker matching is case-insensitive (like the rest of the app). An unknown ticker raises `UnknownTickerError`.
- Raise `ValueError` if `date` is not a trading day in the data (for example a weekend), or if it is the
  first date in the data (there is no previous close).

## API (`stockapp/routes.py`)

- `GET /api/stocks/<ticker>`: keep the existing fields and add `"latest_change"`, equal to `daily_change(ticker)`.
- New `GET /api/stocks/<ticker>/change` with optional query parameter `date`. Returns the `daily_change`
  dict as JSON (status 200).
  - Unknown ticker: status 404 with a JSON body containing an `"error"` key.
  - Invalid `date` (not a trading day, first day, or badly formatted): status 400 with a JSON body containing an `"error"` key.

## UI (`stockapp/templates/index.html`)

In the quote header of the main page, next to the latest close, add an element with `id="day-change"`
that shows the selected stock's latest change in this exact text format:

- `+1.23 (+0.45%)` when the change is zero or positive
- `-2.00 (-1.10%)` when the change is negative

(sign, change with 2 decimals, space, then the percentage with sign and 2 decimals in parentheses).
The element's `class` attribute must include `up` when the change is zero or positive and `down` when it is negative.
Style it green/red to match the chart colours.

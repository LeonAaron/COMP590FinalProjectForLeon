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

# Feature: top movers

Show which stocks moved the most on a trading day.

## Data layer (`stockapp/stocks.py`)

Add `top_movers(date: str | None = None, limit: int = 5) -> list[dict]`.

- `date` is an ISO date (`YYYY-MM-DD`); `None` means the latest date in the data.
- For every ticker in `TICKERS`, compute that day's percentage change versus the previous trading day's close,
  `round((close - prev_close) / prev_close * 100, 2)`.
- Each entry is `{"ticker": ..., "name": ..., "close": ..., "change_pct": ...}`.
- Sort by `change_pct` (the rounded value) from highest to lowest. **Ties** are broken by ticker symbol in
  alphabetical order.
- Return only the first `limit` entries. `limit` must be an `int` from 1 to 5, otherwise raise `ValueError`.
- Raise `ValueError` if `date` is not a trading day in the data or is the first date (no previous close).
- Use `load_prices` from this module to read the data.

## API (`stockapp/routes.py`)

`GET /api/movers` with optional query parameters `date` and `limit` (default 5) returns
`{"date": "<date used>", "movers": [...]}`.
Invalid `date` or `limit` (not a whole number, or out of range): status **400** with an `"error"` key.

## UI

Add a panel `<section id="movers">` to the main page listing the latest day's movers in sorted order. Each entry is an
`<li class="mover" data-ticker="<TICKER>">` containing the ticker and its change formatted with a sign and 2 decimals,
e.g. `+1.23%` or `-0.50%` (a change of exactly zero is shown as `+0.00%`). Entries also get the class `up` (change zero or
positive) or `down` (negative).

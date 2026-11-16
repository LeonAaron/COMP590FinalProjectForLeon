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

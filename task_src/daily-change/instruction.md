## Feature: daily price change

Users want to see at a glance how much the selected stock moved on its latest day.

- Data layer: `daily_change(ticker, date=None)` in `stockapp/stocks.py` returns a dict with keys `date`, `close`,
  `prev_close`, `change` and `change_pct` for the given trading day (latest day when `date` is omitted).
- API: the existing `GET /api/stocks/<ticker>` response gains a `latest_change` field holding that dict for the latest
  day, and a new `GET /api/stocks/<ticker>/change?date=...` returns it for any day.
- UI: the quote header shows the latest change next to the last close in an element with `id="day-change"`, formatted
  like `+1.23 (+0.45%)`, coloured green or red via a class of `up` (zero or positive) or `down` (negative).

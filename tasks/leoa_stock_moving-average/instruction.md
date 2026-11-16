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

# Feature: simple moving average (SMA)

Let users overlay a simple moving average of the closing price on the chart.

## Data layer (`stockapp/stocks.py`)

Add `moving_average(ticker: str, window: int) -> list[dict]`.

- Returns one entry per day **that has a full window**, oldest first: `{"date": "...", "value": ...}`.
  The value for a day is the mean of that day's close and the previous `window - 1` closes, rounded to 2 decimals.
  So the first entry is for the `window`-th trading day, and the list has `len(prices) - window + 1` entries.
- `window` must be an `int` between 2 and the number of trading days (inclusive). Otherwise raise `ValueError`
  (`bool` values are not valid windows).
- Unknown ticker raises `UnknownTickerError` (ticker matching is case-insensitive).

## API (`stockapp/routes.py`)

`GET /api/stocks/<ticker>/sma` with query parameter `window` (default `20`) returns:

```json
{"ticker": "NVDA", "window": 20, "values": [{"date": "...", "value": 123.45}, ...]}
```

- `ticker` is the normalized (upper-case) symbol.
- Status **400** with an `"error"` key if `window` is not a whole number (for example `abc` or `2.5`) or is out of range.
- Status **404** with an `"error"` key for an unknown ticker.

## UI

- Add a checkbox `<input type="checkbox" id="sma-toggle">` to the chart panel of the main page, with a
  `<label for="sma-toggle">` whose text contains `20-day SMA`.
- When the checkbox is checked, `stockapp/static/app.js` fetches `/api/stocks/<ticker>/sma?window=20` and draws
  the SMA as a line on the price chart; unchecking it removes the line.

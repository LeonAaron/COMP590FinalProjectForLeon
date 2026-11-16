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

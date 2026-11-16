# Feature: date-range filtering

Let users look at only part of the price history.

## Data layer (`stockapp/stocks.py`)

Add `prices_between(ticker: str, start: str | None = None, end: str | None = None) -> list[PriceBar]`.

- Returns the bars whose date is between `start` and `end`, **both inclusive**, oldest first. Either bound may
  be `None` (no limit on that side).
- `start`/`end` must be strings in the exact form `YYYY-MM-DD` (4-digit year, 2-digit month and day) and must be
  real calendar dates (`2026-02-30` is invalid). Anything else raises `ValueError`.
- If both are given and `start` is after `end`, raise `ValueError`.
- A valid range that contains no trading days returns an empty list (not an error).
- Unknown tickers raise `UnknownTickerError` (case-insensitive matching).

## API (`stockapp/routes.py`)

Extend `GET /api/stocks/<ticker>` (keep the existing response fields) with optional query parameters:

- `start` and/or `end`: filter `prices` with `prices_between`.
- `range`: one of `1M`, `3M`, `6M`, `1Y` meaning the last 30, 91, 182 or 365 **calendar days** ending at the latest
  date in the data. The result contains the bars whose date is on or after `latest date - N days`.
- With no filter parameters the response is unchanged (all prices).
- Status **400** with an `"error"` key when: a date is invalid, `start` is after `end`, `range` is not one of the
  four values, or `range` is combined with `start` or `end`.
- A valid filter that matches no days returns status 200 with `"prices": []`.
- Unknown ticker is still status 404.

## UI

- In the chart panel of the main page add four buttons, in this order:
  `<button class="range-btn" data-range="1M">1M</button>`, then `3M`, `6M`, `1Y` the same way.
  The `1Y` button also has the class `active` on page load.
- `stockapp/static/app.js` reloads the chart with `/api/stocks/<ticker>?range=<value>` when a button is clicked and
  moves the `active` class to the clicked button.

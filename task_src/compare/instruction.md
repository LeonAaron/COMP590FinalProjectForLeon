# Feature: compare stocks

Let users compare the relative performance of several stocks on one chart.

## Data layer (`stockapp/stocks.py`)

Add `compare(tickers: list[str]) -> dict` that returns:

```json
{"tickers": ["NVDA", "MSFT"], "dates": ["2025-11-17", ...], "series": {"NVDA": [100.0, ...], "MSFT": [100.0, ...]}}
```

- `tickers`: the normalized symbols in the order given.
- `dates`: the dates that are present for **every** requested ticker, oldest first.
- `series[T]`: for each of those dates, that day's close divided by T's close on the first common date, times 100,
  rounded to 2 decimals. So every series starts at exactly `100.0`.
- Validation (raise `ValueError`): fewer than 2 or more than 5 tickers, or the same ticker more than once
  (case-insensitive, so `["nvda", "NVDA"]` is a duplicate). Unknown tickers raise `UnknownTickerError`.

## API (`stockapp/routes.py`)

`GET /api/compare?tickers=NVDA,msft` returns the `compare` result as JSON.

- `tickers` is a comma-separated list; whitespace around each symbol is ignored, and empty items
  (e.g. from a trailing comma) are ignored.
- Status **400** with an `"error"` key when the parameter is missing, when there are fewer than 2 or more than 5
  tickers, when there is a duplicate, or when any ticker is unknown.

## UI

- New page `GET /compare` (HTML, status 200) using the same header/styling as the main page.
  - Optional query parameter `tickers` (same format as the API). When it is missing or invalid, the page compares
    all five stocks.
  - The page contains `<div id="compare-chart" data-tickers="NVDA,MSFT">` (the normalized symbols actually compared,
    comma-separated, no spaces) and JavaScript that draws one line per ticker from `/api/compare`.
  - Below the chart, `<table id="compare-table">` with one `<tr data-ticker="<TICKER>">` per compared ticker (in order)
    whose cells are the symbol and the ticker's **last** normalized value with 2 decimals (e.g. `142.37`).
- The main page has a link to the comparison page: an `<a>` whose `href` starts with `/compare`.

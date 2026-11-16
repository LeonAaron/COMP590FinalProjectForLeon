## Feature: moving average overlay

Users want to smooth out the price chart with a simple moving average (SMA) of the close.

- Data layer: `moving_average(ticker, window)` returns `[{"date": ..., "value": ...}, ...]`, one entry per day that has a
  full window of closes ending on that day. Sensible windows are at least 2 days and no longer than the data.
- API: `GET /api/stocks/<ticker>/sma?window=N` (default window 20) returns `{"ticker", "window", "values"}`.
- UI: a checkbox `id="sma-toggle"` labelled `20-day SMA` in the chart panel; when ticked, `static/app.js` fetches the
  SMA endpoint and draws the line on the chart.

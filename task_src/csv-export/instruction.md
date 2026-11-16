## Feature: CSV export

Users want to download a stock's history to open in a spreadsheet.

- `GET /api/stocks/<ticker>/export.csv` downloads (as an attachment named `<TICKER>_prices.csv`) a `text/csv` file
  with columns `date,open,high,low,close,volume,change_pct`, one row per trading day. Prices have 2 decimals, volume is
  a whole number, and `change_pct` is the day's change versus the previous close (left empty when there is none).
- Optional `order=asc|desc` (default `asc`, oldest first). Reversing the order must not change what each row's
  `change_pct` means.
- UI: an `<a id="export-link" ... download>` in the chart panel pointing at the selected stock's export.

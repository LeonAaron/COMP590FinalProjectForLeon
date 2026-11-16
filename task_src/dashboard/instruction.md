## Feature: market summary dashboard

Users want one page that summarizes every stock.

- Data layer: `summary_stats(ticker)` returns `ticker`, `name`, `last_close`, `high_52w` (highest high), `low_52w`
  (lowest low), `avg_volume` (mean daily volume as a whole number), `return_1y_pct` (first close to last close) and
  `volatility_pct` (annualized), all over the full data set.
- API: `GET /api/summary` lists `summary_stats` for every ticker in `TICKERS` order.
- UI: a `/dashboard` page (page name: `Dashboard`) with `<table id="summary-table">`, columns `Symbol`, `Last Close`, `52W High`, `52W Low`,
  `Avg Volume`, `1Y Return`, `Volatility`, and one `<tr data-ticker="...">` per stock. Volumes use thousands separators;
  the return is signed; the volatility is a plain percentage. The main page links to it (`href="/dashboard"`).

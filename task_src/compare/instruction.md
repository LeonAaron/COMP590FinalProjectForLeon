## Feature: compare stocks

Users want to compare the relative performance of 2 to 5 different stocks.

- Data layer: `compare(tickers)` returns `{"tickers", "dates", "series"}`: the symbols in the order given, the dates
  every one of them has, and per ticker its closes rebased so its first common date is exactly 100.
- API: `GET /api/compare?tickers=NVDA,msft` (comma-separated; blanks around or between commas are ignored).
- UI: a `/compare` page (optional `tickers` parameter; it falls back to all five stocks when the parameter is missing
  or unusable) with `<div id="compare-chart" data-tickers="NVDA,MSFT">` drawn by JavaScript, and a
  `<table id="compare-table">` with one `<tr data-ticker="...">` per stock showing its symbol and final rebased value.
  The main page links to it (an `href` starting with `/compare`).

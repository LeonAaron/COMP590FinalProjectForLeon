You are working on a small Flask web app in `/app` called **Stock Chart Viewer**.
It shows one year of daily prices for five stocks (NVDA, MSFT, AAPL, GOOGL, META)
read from bundled CSV files in `stockapp/data/`.

- `stockapp/stocks.py` is the data layer (`TICKERS`, `PriceBar`, `load_prices`, `latest_bar`, `normalize_ticker`, `UnknownTickerError`).
- `stockapp/routes.py` holds the HTTP routes (a Flask blueprint registered by `create_app()` in `stockapp/__init__.py`).
- `stockapp/templates/index.html` is the main page; `stockapp/static/` holds its JavaScript and CSS.
- `tests/` holds the existing tests. Run them from `/app` with `python -m pytest`. They must keep passing.

Do not change the CSV data files or break existing behaviour. Use only the Python
standard library and Flask (no new dependencies, no network access at runtime).

This release adds several features, described below. Your work will be checked by automated tests
that exercise the names, routes, JSON fields and HTML element ids given in the descriptions, and
that expect the codebase conventions below to hold everywhere.

## Codebase conventions (apply to every feature)

- **Tickers** are case-insensitive and ignore surrounding whitespace wherever a user supplies one (URL path,
  query string, JSON body, Python argument). Output always uses the upper-case symbol.
- **Data-layer functions** raise `UnknownTickerError` for unknown tickers and `ValueError` for any other invalid
  argument (wrong type, out of range, a date that is not usable, ...). `bool` is never accepted where a number is expected.
- **JSON API errors** return a JSON object with an `"error"` key. Use status **404** when the resource named in the
  URL path does not exist (unknown ticker in the path, unknown id), and **400** for any other invalid input (bad or missing
  query parameters, malformed or wrongly typed JSON bodies, unknown tickers given in a query string or body).
- **Dates** are strings in exactly `YYYY-MM-DD` form and must be real calendar dates. "The previous close" always means the
  close of the previous trading day present in the data; the oldest day has no previous close.
- **Numbers**: computed prices and percentages are rounded to 2 decimals (round the final value, not intermediate
  steps). A percentage change is `(new - old) / old * 100`. In HTML, prices and percentages are shown with exactly 2
  decimals, and signed changes always carry an explicit sign (`+1.20`, `-0.35%`, zero shown as `+0.00`).
- **Annualized volatility** is the sample standard deviation of daily log returns `ln(close_t / close_{t-1})`, times
  `sqrt(252)`, times 100.
- **New pages** reuse the main page's header (`<header class="topbar">` containing the `brand` link back to `/`) and
  stylesheet, and their `<title>` is `<page name> · Stock Chart Viewer` (the page name is given with each feature).
- **New API endpoints** (every new route under `/api/`) send the header `Cache-Control: no-store` on successful
  responses, because prices and user data must never be served stale.
- **Server rendering**: new panels, tables and lists show their content in the HTML the server returns (JavaScript may
  enhance the page, but the content must not depend on it).
- **Accessibility**: every new `<table>` has a `<caption>`, and every new panel `<section>` added to a page has an
  `aria-label` describing it.

---

## Feature: date-range filtering

Users want to zoom the chart to part of the year.

- Data layer: `prices_between(ticker, start=None, end=None)` returns the `PriceBar`s between the two dates, both
  inclusive; either bound may be omitted. A valid range with no trading days in it is simply empty.
- API: `GET /api/stocks/<ticker>` accepts optional `start`/`end` query parameters, or instead a `range` of `1M`, `3M`,
  `6M` or `1Y`: the days on or after the date that is 30, 91, 182 or 365 calendar days before the latest date in the
  data. `range` cannot be
  combined with `start`/`end`. Without these parameters the response is unchanged.
- UI: four buttons `<button class="range-btn" data-range="1M">1M</button>` (then 3M, 6M, 1Y) in the chart panel, with
  `1Y` marked `active` initially; `static/app.js` reloads the chart for the clicked range and moves the `active` class.

## Feature: compare stocks

Users want to compare the relative performance of 2 to 5 different stocks.

- Data layer: `compare(tickers)` returns `{"tickers", "dates", "series"}`: the symbols in the order given, the dates
  every one of them has, and per ticker its closes rebased so its first common date is exactly 100.
- API: `GET /api/compare?tickers=NVDA,msft` (comma-separated; blanks around or between commas are ignored).
- UI: a `/compare` page (page name: `Compare`; optional `tickers` parameter; it falls back to all five stocks when the parameter is missing
  or unusable) with `<div id="compare-chart" data-tickers="NVDA,MSFT">` drawn by JavaScript, and a
  `<table id="compare-table">` with one `<tr data-ticker="...">` per stock showing its symbol and final rebased value.
  The main page links to it (an `href` starting with `/compare`).

## Feature: price alerts

Users want to set alerts such as "tell me when NVDA is above 150" and see which have been hit.

- Alerts live in memory and belong to one app instance (`create_app()` starts with none; instances never share
  alerts). Each has an integer `id` (1, 2, 3, ... per instance, never reused), `ticker`, `direction` (`above` or
  `below`), a positive `price`, and `triggered`, which is true when the latest close is at or beyond the price in that
  direction.
- API: `POST /api/alerts` (body `{"ticker", "direction", "price"}`) creates one and answers 201 with the alert;
  `GET /api/alerts` lists them in creation order (optional `ticker` filter) as `{"alerts": [...]}`;
  `DELETE /api/alerts/<id>` answers 204 with an empty body.
- UI: a `<section id="alerts">` in the main page's server-rendered HTML (not filled in later by JavaScript) lists the
  selected stock's alerts as
  `<li class="alert-item" data-alert-id="...">` showing e.g. `above 150.00`, with an extra `triggered` class when hit,
  or says `No alerts for <TICKER>`.

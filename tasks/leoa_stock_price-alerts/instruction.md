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

# Feature: price alerts

Let users set price alerts and see whether they have been triggered by the latest close.

## Behaviour

- Alerts are kept **in memory, per app instance**: every app returned by `create_app()` starts with no alerts, and
  alerts created through one app instance are not visible in another.
- Each alert has: `id` (an `int`; the first alert of an app instance is `1`, then `2`, ... — ids are never reused within
  an instance), `ticker` (normalized symbol), `direction` (`"above"` or `"below"`), `price` (a number greater than 0,
  returned as a float) and `triggered` (bool).
- `triggered` is computed from the **latest close** of the ticker: for `above`, latest close `>=` price; for `below`,
  latest close `<=` price.

## API (`stockapp/routes.py`)

All responses are JSON unless noted.

- `POST /api/alerts` with body `{"ticker": "nvda", "direction": "above", "price": 150}` creates an alert and returns it
  with status **201**.
  Status **400** with an `"error"` key when: the body is not a JSON object; `ticker` is missing, not a string or unknown;
  `direction` is not exactly `"above"` or `"below"`; `price` is missing, not a number (booleans and strings are not
  numbers), or not greater than 0.
- `GET /api/alerts` returns `{"alerts": [...]}` in creation order. Optional `ticker` query parameter filters to one
  ticker (case-insensitive); an unknown ticker in the filter is status 400 with an `"error"` key.
- `DELETE /api/alerts/<id>` deletes the alert and returns status **204** with an empty body; status **404** with an
  `"error"` key if there is no alert with that id.

## UI

Add a panel `<section id="alerts">` to the main page listing the alerts **for the selected ticker**. Each alert is an
`<li class="alert-item" data-alert-id="<id>">` that shows the direction and the price with 2 decimals
(e.g. `above 150.00`), and also has the class `triggered` when the alert is triggered. When the selected ticker has no
alerts, the panel shows the text `No alerts for <TICKER>` (e.g. `No alerts for NVDA`).

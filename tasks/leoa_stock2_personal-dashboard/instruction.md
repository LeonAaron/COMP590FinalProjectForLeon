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
- New pages reuse the main page's header and stylesheet so they look like part of the same app.

---

## Feature: top movers

Users want to know which stocks moved most on a given day.

- Data layer: `top_movers(date=None, limit=5)` in `stockapp/stocks.py` returns entries
  `{"ticker", "name", "close", "change_pct"}` for every tracked stock on that day (latest day by default), biggest gain
  first, ties broken alphabetically by ticker, cut to `limit` (1 to 5). Read prices through this module's `load_prices`.
- API: `GET /api/movers?date=...&limit=...` returns `{"date": <day used>, "movers": [...]}`.
- UI: a `<section id="movers">` on the main page lists the latest day's movers in order, each as
  `<li class="mover" data-ticker="...">` showing the signed percentage (e.g. `+1.23%`) and carrying an `up`/`down` class.

## Feature: watchlist

Users want a personal watchlist that survives restarts.

- Storage lives in a new module `stockapp/watchlist.py` with `load_watchlist()`, `add_to_watchlist(ticker)` and
  `remove_from_watchlist(ticker)`, each returning the resulting list of symbols (insertion order, no duplicates).
  Removing a ticker that is not on the list raises `KeyError`.
- The list is saved as a JSON array in the file named by the `WATCHLIST_PATH` environment variable (default
  `stockapp/data/watchlist.json`). Tests point this variable at different files while the app is running, so honour
  its current value every time. A missing file is an empty watchlist.
- API: `GET /api/watchlist`, `POST /api/watchlist` (body `{"ticker": "..."}`) and `DELETE /api/watchlist/<ticker>`,
  all answering `{"tickers": [...]}`. A POST that actually adds a ticker answers 201; one that changes nothing answers 200.
  Deleting a ticker that is not on the list is a 404.
- UI: a `<section id="watchlist">` on the main page lists each saved ticker as an element with class `watchlist-item` and
  `data-ticker="<TICKER>"`, or says `Your watchlist is empty`.

## Feature: daily price change

Users want to see at a glance how much the selected stock moved on its latest day.

- Data layer: `daily_change(ticker, date=None)` in `stockapp/stocks.py` returns a dict with keys `date`, `close`,
  `prev_close`, `change` and `change_pct` for the given trading day (latest day when `date` is omitted).
- API: the existing `GET /api/stocks/<ticker>` response gains a `latest_change` field holding that dict for the latest
  day, and a new `GET /api/stocks/<ticker>/change?date=...` returns it for any day.
- UI: the quote header shows the latest change next to the last close in an element with `id="day-change"`, formatted
  like `+1.23 (+0.45%)`, coloured green or red via a class of `up` (zero or positive) or `down` (negative).

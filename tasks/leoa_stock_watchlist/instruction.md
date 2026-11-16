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

# Feature: watchlist

Let users keep a personal watchlist of stocks that is saved to disk.

## Storage (new module `stockapp/watchlist.py`)

- The watchlist is stored as a JSON array of ticker symbols, e.g. `["NVDA", "AAPL"]`.
- The file path comes from the environment variable `WATCHLIST_PATH`, **read each time the watchlist is
  loaded or saved** (not once at import). When the variable is not set, use `stockapp/data/watchlist.json`.
- A missing file means an empty watchlist. Create the file (and its parent directory) when saving.
- Provide these functions:
  - `load_watchlist() -> list[str]`
  - `add_to_watchlist(ticker: str) -> list[str]`: normalizes the ticker (case-insensitive, surrounding
    whitespace ignored), raises `UnknownTickerError` for tickers not in `TICKERS`, appends it to the end if it
    is not already present (adding an existing ticker changes nothing), saves, and returns the new list.
  - `remove_from_watchlist(ticker: str) -> list[str]`: removes the ticker (case-insensitive), saves, and returns
    the new list. Raises `KeyError` if the ticker is not in the watchlist.
- Order is insertion order.

## API (`stockapp/routes.py`)

All responses are JSON.

- `GET /api/watchlist` returns `{"tickers": [...]}`.
- `POST /api/watchlist` with a JSON body `{"ticker": "msft"}` adds the ticker.
  - Returns `{"tickers": [...]}` with status **201** when it was added, or status **200** when it was already present.
  - Returns status **400** with an `"error"` key when the body is not a JSON object, the `ticker` field is
    missing or not a string, or the ticker is unknown.
- `DELETE /api/watchlist/<ticker>` removes the ticker and returns `{"tickers": [...]}` with status 200.
  Returns status **404** with an `"error"` key if the ticker is not in the watchlist.

## UI (`stockapp/templates/index.html`)

Add a panel `<section id="watchlist">` to the main page that lists the watchlist in order. Each entry is an
element with `class="watchlist-item"` and a `data-ticker="<TICKER>"` attribute, showing the ticker and its
latest close. When the watchlist is empty, the panel shows the text `Your watchlist is empty`.

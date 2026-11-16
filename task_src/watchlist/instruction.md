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

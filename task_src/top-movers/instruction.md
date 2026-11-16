## Feature: top movers

Users want to know which stocks moved most on a given day.

- Data layer: `top_movers(date=None, limit=5)` in `stockapp/stocks.py` returns entries
  `{"ticker", "name", "close", "change_pct"}` for every tracked stock on that day (latest day by default), biggest gain
  first, ties broken alphabetically by ticker, cut to `limit` (1 to 5). Read prices through this module's `load_prices`.
- API: `GET /api/movers?date=...&limit=...` returns `{"date": <day used>, "movers": [...]}`.
- UI: a `<section id="movers">` on the main page lists the latest day's movers in order, each as
  `<li class="mover" data-ticker="...">` showing the signed percentage (e.g. `+1.23%`) and carrying an `up`/`down` class.

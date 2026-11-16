## Feature: price alerts

Users want to set alerts such as "tell me when NVDA is above 150" and see which have been hit.

- Alerts live in memory and belong to one app instance (`create_app()` starts with none; instances never share
  alerts). Each has an integer `id` (1, 2, 3, ... per instance, never reused), `ticker`, `direction` (`above` or
  `below`), a positive `price`, and `triggered`, which is true when the latest close is at or beyond the price in that
  direction.
- API: `POST /api/alerts` (body `{"ticker", "direction", "price"}`) creates one and answers 201 with the alert;
  `GET /api/alerts` lists them in creation order (optional `ticker` filter) as `{"alerts": [...]}`;
  `DELETE /api/alerts/<id>` answers 204 with an empty body.
- UI: a `<section id="alerts">` on the main page lists the selected stock's alerts as
  `<li class="alert-item" data-alert-id="...">` showing e.g. `above 150.00`, with an extra `triggered` class when hit,
  or says `No alerts for <TICKER>`.

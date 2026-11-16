## Feature: date-range filtering

Users want to zoom the chart to part of the year.

- Data layer: `prices_between(ticker, start=None, end=None)` returns the `PriceBar`s between the two dates, both
  inclusive; either bound may be omitted. A valid range with no trading days in it is simply empty.
- API: `GET /api/stocks/<ticker>` accepts optional `start`/`end` query parameters, or instead a `range` of `1M`, `3M`,
  `6M` or `1Y` meaning the last 30, 91, 182 or 365 calendar days up to the latest date in the data. `range` cannot be
  combined with `start`/`end`. Without these parameters the response is unchanged.
- UI: four buttons `<button class="range-btn" data-range="1M">1M</button>` (then 3M, 6M, 1Y) in the chart panel, with
  `1Y` marked `active` initially; `static/app.js` reloads the chart for the clicked range and moves the `active` class.

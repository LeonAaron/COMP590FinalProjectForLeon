## Feature: analysis report

Users want a short written report on a stock that they can read in the app or download as Markdown.

- `generate_report(ticker)` in a new module `stockapp/report.py` returns this Markdown (blocks separated by one blank
  line, ending with a newline):

  ```
  # {company name} ({TICKER}) Analysis Report

  ## Price Summary
  - Last close: ${close} (as of {date})
  - 52-week high: ${highest high}
  - 52-week low: ${lowest low}

  ## Performance
  - 1-year return: {first close to last close}%
  - 1-month return: {close 21 trading days before the last one, to the last close}%

  ## Volatility
  - Annualized volatility: {volatility}%

  ## Trend
  - 50-day SMA: ${mean of the last 50 closes}
  - Trend: {Bullish | Bearish | Neutral}
  ```

  The trend is Bullish when the last close is above the 50-day SMA, Bearish when below, Neutral when equal.
  Money is written like `$1234.50`; returns are signed.
- `GET /api/stocks/<ticker>/report.md` serves the Markdown as `text/markdown`.
- `GET /report/<ticker>` (page name: `<TICKER> Analysis Report`, e.g. `NVDA Analysis Report`) renders it as HTML inside `<article id="report">` (title as `<h1>`, sections as `<h2>`, bullets
  as `<li>`), and the main page links to the selected stock's report with `<a id="report-link">`.

# Stock Chart Viewer (baseline app)

A small Flask app that shows one year of daily candlestick charts (with volume) for
NVIDIA (NVDA), Microsoft (MSFT), Apple (AAPL), Alphabet/Google (GOOGL) and Meta (META).

This is the **baseline codebase** for the evaluation. The single agent and the
multi-agent team each start from this exact code and are asked to add features
such as a watchlist, a dashboard or an analysis report.

## Run

```bash
cd app
uv sync
uv run flask --app stockapp run --debug   # http://127.0.0.1:5000 (--debug reloads templates on edit)
uv run pytest                        # existing tests (must keep passing after any feature)
```

## Layout

| Path | Purpose |
|---|---|
| `stockapp/stocks.py` | Data layer: `TICKERS`, `PriceBar`, `load_prices()`, `latest_bar()` |
| `stockapp/routes.py` | `GET /` (page), `GET /api/stocks`, `GET /api/stocks/<ticker>` |
| `stockapp/templates/index.html` | Page with a ticker selector (`#ticker-select`), symbol list, quote header, and chart container (`#price-chart`) |
| `stockapp/static/app.js` | Fetches `/api/stocks/<ticker>` and draws candlesticks + volume with TradingView [lightweight-charts](https://github.com/tradingview/lightweight-charts) 4.2.0 (Apache-2.0, bundled in `static/vendor/` so the app works offline) |
| `stockapp/data/*.csv` | Price snapshot: `date,open,high,low,close,volume`, oldest first |
| `scripts/fetch_data.py` | Regenerates the snapshot from Yahoo Finance's public chart endpoint |

## Why a data snapshot instead of a live API

Evaluation runs must be **deterministic** (the same task gets the same expected
answers every time), and the Harbor sandboxes have no network access. So the app
reads bundled CSVs. The current snapshot covers 250 completed trading sessions,
2025-11-17 to 2026-11-13. Only rerun `scripts/fetch_data.py` before task
expected values are written, never after.

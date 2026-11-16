import math
import re
import statistics

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected(ticker: str) -> dict:
    bars = stocks.load_prices(ticker)
    closes = [b.close for b in bars]
    logs = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    return {
        "ticker": ticker,
        "name": stocks.TICKERS[ticker],
        "last_close": closes[-1],
        "high_52w": max(b.high for b in bars),
        "low_52w": min(b.low for b in bars),
        "avg_volume": round(sum(b.volume for b in bars) / len(bars)),
        "return_1y_pct": round((closes[-1] / closes[0] - 1) * 100, 2),
        "volatility_pct": round(statistics.stdev(logs) * math.sqrt(252) * 100, 2),
    }


def assert_stats(actual: dict, want: dict) -> None:
    assert set(actual) == set(want)
    assert actual["ticker"] == want["ticker"]
    assert actual["name"] == want["name"]
    assert actual["avg_volume"] == want["avg_volume"]
    assert isinstance(actual["avg_volume"], int)
    for key in ("last_close", "high_52w", "low_52w", "return_1y_pct", "volatility_pct"):
        assert actual[key] == pytest.approx(want[key], abs=0.006), key


@pytest.mark.parametrize("ticker", list(stocks.TICKERS))
def test_summary_stats(ticker: str) -> None:
    assert_stats(stocks.summary_stats(ticker.lower()), expected(ticker))


def test_volatility_uses_sample_std_of_log_returns() -> None:
    want = expected("NVDA")["volatility_pct"]
    assert stocks.summary_stats("NVDA")["volatility_pct"] == pytest.approx(want, abs=0.006)


def test_summary_unknown_ticker() -> None:
    with pytest.raises(stocks.UnknownTickerError):
        stocks.summary_stats("TSLA")


def test_api_summary(client: FlaskClient) -> None:
    resp = client.get("/api/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert [d["ticker"] for d in data] == list(stocks.TICKERS)
    for d in data:
        assert_stats(d, expected(d["ticker"]))


def table(client: FlaskClient) -> str:
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    match = re.search(r'<table[^>]*\bid="summary-table"[^>]*>(.*?)</table>', resp.get_data(as_text=True), re.S)
    assert match, "no <table id=summary-table>"
    return match.group(1)


def cells(fragment: str, tag: str) -> list[str]:
    return [" ".join(re.sub(r"<[^>]+>", "", c).split()) for c in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", fragment, re.S)]


def test_dashboard_headers(client: FlaskClient) -> None:
    assert cells(table(client), "th")[:7] == [
        "Symbol", "Last Close", "52W High", "52W Low", "Avg Volume", "1Y Return", "Volatility",
    ]


def test_dashboard_rows_in_order(client: FlaskClient) -> None:
    rows = re.findall(r'<tr[^>]*\bdata-ticker="([A-Z]+)"', table(client))
    assert rows == list(stocks.TICKERS)


@pytest.mark.parametrize("ticker", list(stocks.TICKERS))
def test_dashboard_row_values(client: FlaskClient, ticker: str) -> None:
    want = expected(ticker)
    row = re.search(rf'<tr[^>]*\bdata-ticker="{ticker}"[^>]*>(.*?)</tr>', table(client), re.S)
    assert row
    assert [c.removeprefix("$") for c in cells(row.group(1), "t[hd]")] == [  # "$" prefix is allowed
        ticker,
        f"{want['last_close']:.2f}",
        f"{want['high_52w']:.2f}",
        f"{want['low_52w']:.2f}",
        f"{want['avg_volume']:,}",
        f"{want['return_1y_pct']:+.2f}%",
        f"{want['volatility_pct']:.2f}%",
    ]


def test_index_links_to_dashboard(client: FlaskClient) -> None:
    assert re.search(r'<a[^>]*\bhref="/dashboard"', client.get("/").get_data(as_text=True))

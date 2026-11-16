import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected(index: int = -1, limit: int = 5) -> list[dict]:
    rows = []
    for t, name in stocks.TICKERS.items():
        bars = stocks.load_prices(t)
        close, prev = bars[index].close, bars[index - 1].close
        rows.append({"ticker": t, "name": name, "close": close, "change_pct": round((close - prev) / prev * 100, 2)})
    rows.sort(key=lambda r: (-r["change_pct"], r["ticker"]))
    return rows[:limit]


def assert_movers(actual: list[dict], want: list[dict]) -> None:
    assert [a["ticker"] for a in actual] == [w["ticker"] for w in want]
    for a, w in zip(actual, want):
        assert set(a) == {"ticker", "name", "close", "change_pct"}
        assert a["name"] == w["name"]
        assert a["close"] == pytest.approx(w["close"], abs=0.006)
        assert a["change_pct"] == pytest.approx(w["change_pct"], abs=0.006)


def test_function_latest() -> None:
    assert_movers(stocks.top_movers(), expected())


def test_function_specific_date_and_limit() -> None:
    date = stocks.load_prices("NVDA")[120].date
    assert_movers(stocks.top_movers(date, limit=3), expected(120, 3))


@pytest.mark.parametrize("limit", [0, 6, -1, True])
def test_function_bad_limit(limit: int) -> None:
    with pytest.raises(ValueError):
        stocks.top_movers(limit=limit)


@pytest.mark.parametrize("date", ["2026-11-14", "2025-11-17"])
def test_function_bad_date(date: str) -> None:
    with pytest.raises(ValueError):
        stocks.top_movers(date)


def test_function_ties_break_alphabetically(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake(ticker: str):
        symbol = stocks.normalize_ticker(ticker)
        last = {"NVDA": 102.0, "MSFT": 101.0, "AAPL": 102.0, "GOOGL": 99.0, "META": 101.0}[symbol]
        return (
            stocks.PriceBar("2026-01-02", 100.0, 100.0, 100.0, 100.0, 1),
            stocks.PriceBar("2026-01-05", 100.0, last, 99.0, last, 1),
        )

    monkeypatch.setattr(stocks, "load_prices", fake)
    assert [r["ticker"] for r in stocks.top_movers()] == ["AAPL", "NVDA", "META", "MSFT", "GOOGL"]


def test_api_default(client: FlaskClient) -> None:
    resp = client.get("/api/movers")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["date"] == stocks.load_prices("NVDA")[-1].date
    assert_movers(data["movers"], expected())


def test_api_date_and_limit(client: FlaskClient) -> None:
    date = stocks.load_prices("NVDA")[60].date
    data = client.get(f"/api/movers?date={date}&limit=2").get_json()
    assert data["date"] == date
    assert_movers(data["movers"], expected(60, 2))


@pytest.mark.parametrize("query", ["limit=0", "limit=6", "limit=two", "limit=2.5", "date=2026-11-14", "date=bad"])
def test_api_invalid_is_400(client: FlaskClient, query: str) -> None:
    assert client.get("/api/movers").status_code == 200  # endpoint exists
    resp = client.get(f"/api/movers?{query}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_ui_movers_panel(client: FlaskClient) -> None:
    page = client.get("/").get_data(as_text=True)
    panel = re.search(r'<section[^>]*\bid="movers"[^>]*>(.*?)</section>', page, re.S)
    assert panel, "no <section id=movers>"
    items = re.findall(r'<li([^>]*)>(.*?)</li>', panel.group(1), re.S)
    items = [(a, b) for a, b in items if re.search(r'class="[^"]*\bmover\b', a)]
    want = expected()
    assert [re.search(r'data-ticker="([A-Z]+)"', a).group(1) for a, _ in items] == [w["ticker"] for w in want]
    for (attrs, body), w in zip(items, want):
        text = " ".join(re.sub(r"<[^>]+>", " ", body).split())
        assert f"{w['change_pct']:+.2f}%" in text
        classes = re.search(r'class="([^"]*)"', attrs).group(1).split()
        assert ("up" if w["change_pct"] >= 0 else "down") in classes

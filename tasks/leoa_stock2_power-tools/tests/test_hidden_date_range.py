import datetime as dt
import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def dates(bars) -> list[str]:
    return [b.date if hasattr(b, "date") else b["date"] for b in bars]


def all_dates(ticker: str = "NVDA") -> list[str]:
    return dates(stocks.load_prices(ticker))


def test_function_inclusive_bounds() -> None:
    d = all_dates()
    got = stocks.prices_between("nvda", d[10], d[20])
    assert dates(got) == d[10:21]
    assert all(isinstance(b, stocks.PriceBar) for b in got)


def test_function_open_ended() -> None:
    d = all_dates("AAPL")
    assert dates(stocks.prices_between("AAPL", start=d[-5])) == d[-5:]
    assert dates(stocks.prices_between("AAPL", end=d[4])) == d[:5]
    assert dates(stocks.prices_between("AAPL")) == d


def test_function_weekend_bounds_and_empty() -> None:
    d = all_dates()
    assert dates(stocks.prices_between("NVDA", "2026-11-14", "2026-11-15")) == []
    assert dates(stocks.prices_between("NVDA", "2026-11-07", "2026-11-13")) == [x for x in d if "2026-11-07" <= x <= "2026-11-13"]


@pytest.mark.parametrize(
    ("start", "end"),
    [("2026-02-30", None), ("2026/01/05", None), ("20260105", None), (None, "2026-1-5"), ("2026-06-01", "2026-05-01")],
)
def test_function_invalid(start, end) -> None:
    with pytest.raises(ValueError):
        stocks.prices_between("NVDA", start, end)


def test_api_start_end(client: FlaskClient) -> None:
    d = all_dates("MSFT")
    resp = client.get(f"/api/stocks/MSFT?start={d[3]}&end={d[7]}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ticker"] == "MSFT"
    assert dates(data["prices"]) == d[3:8]
    # no filter parameters -> unchanged
    assert dates(client.get("/api/stocks/MSFT").get_json()["prices"]) == d


@pytest.mark.parametrize(("rng", "days"), [("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365)])
def test_api_range(client: FlaskClient, rng: str, days: int) -> None:
    d = all_dates("GOOGL")
    assert len(client.get("/api/stocks/GOOGL?range=1M").get_json()["prices"]) < len(d)  # filtering works
    cutoff =(dt.date.fromisoformat(d[-1]) - dt.timedelta(days=days)).isoformat()
    resp = client.get(f"/api/stocks/GOOGL?range={rng}")
    assert resp.status_code == 200
    assert dates(resp.get_json()["prices"]) == [x for x in d if x >= cutoff]


def test_api_empty_range_is_200(client: FlaskClient) -> None:
    resp = client.get("/api/stocks/NVDA?start=2026-11-14&end=2026-11-15")
    assert resp.status_code == 200
    assert resp.get_json()["prices"] == []


@pytest.mark.parametrize(
    "query",
    ["start=2026-02-30", "end=yesterday", "start=2026-06-01&end=2026-05-01", "range=2Y",
     "range=1M&start=2026-01-05"],
)
def test_api_bad_params_are_400(client: FlaskClient, query: str) -> None:
    assert client.get("/api/stocks/NVDA?range=1M").status_code == 200
    resp = client.get(f"/api/stocks/NVDA?{query}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_ui_range_buttons(client: FlaskClient) -> None:
    page = client.get("/").get_data(as_text=True)
    buttons = re.findall(r'<button([^>]*)>\s*([^<]*?)\s*</button>', page)
    ranged = [(attrs, text) for attrs, text in buttons if "range-btn" in attrs]
    assert [re.search(r'data-range="([^"]+)"', a).group(1) for a, _ in ranged] == ["1M", "3M", "6M", "1Y"]
    assert [t for _, t in ranged] == ["1M", "3M", "6M", "1Y"]
    active = [re.search(r'data-range="([^"]+)"', a).group(1) for a, _ in ranged
              if "active" in re.search(r'class="([^"]*)"', a).group(1).split()]
    assert active == ["1Y"]


def test_js_uses_range_param(client: FlaskClient) -> None:
    js = client.get("/static/app.js").get_data(as_text=True)
    assert "range-btn" in js
    assert "range=" in js

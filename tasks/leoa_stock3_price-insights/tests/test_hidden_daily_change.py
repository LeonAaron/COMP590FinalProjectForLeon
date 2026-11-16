import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected(ticker: str, index: int) -> dict:
    bars = stocks.load_prices(ticker)
    close, prev = bars[index].close, bars[index - 1].close
    return {
        "date": bars[index].date,
        "close": close,
        "prev_close": prev,
        "change": round(close - prev, 2),
        "change_pct": round((close - prev) / prev * 100, 2),
    }


def assert_change(actual: dict, want: dict) -> None:
    assert set(actual) == set(want)
    assert actual["date"] == want["date"]
    for key in ("close", "prev_close", "change", "change_pct"):
        assert actual[key] == pytest.approx(want[key], abs=0.006), key


def test_function_defaults_to_latest_day() -> None:
    assert_change(stocks.daily_change("NVDA"), expected("NVDA", -1))


def test_function_specific_date_and_case_insensitive() -> None:
    bars = stocks.load_prices("AAPL")
    assert_change(stocks.daily_change("aapl", bars[100].date), expected("AAPL", 100))


def test_function_second_day_is_valid() -> None:
    bars = stocks.load_prices("MSFT")
    assert_change(stocks.daily_change("MSFT", bars[1].date), expected("MSFT", 1))


def test_function_first_day_raises() -> None:
    first = stocks.load_prices("MSFT")[0].date
    with pytest.raises(ValueError):
        stocks.daily_change("MSFT", first)


def test_function_non_trading_day_raises() -> None:
    with pytest.raises(ValueError):
        stocks.daily_change("MSFT", "2026-11-14")  # a Saturday


def test_function_unknown_ticker() -> None:
    with pytest.raises(stocks.UnknownTickerError):
        stocks.daily_change("TSLA")


def test_api_prices_include_latest_change(client: FlaskClient) -> None:
    data = client.get("/api/stocks/meta").get_json()
    assert len(data["prices"]) == len(stocks.load_prices("META"))
    assert_change(data["latest_change"], expected("META", -1))


def test_api_change_endpoint_with_date(client: FlaskClient) -> None:
    date = stocks.load_prices("GOOGL")[42].date
    resp = client.get(f"/api/stocks/GOOGL/change?date={date}")
    assert resp.status_code == 200
    assert_change(resp.get_json(), expected("GOOGL", 42))


def test_api_change_endpoint_default_latest(client: FlaskClient) -> None:
    resp = client.get("/api/stocks/nvda/change")
    assert resp.status_code == 200
    assert_change(resp.get_json(), expected("NVDA", -1))


@pytest.mark.parametrize("date", ["2026-11-14", "2025-11-17", "not-a-date", "2026-13-01"])
def test_api_change_bad_date_is_400(client: FlaskClient, date: str) -> None:
    resp = client.get(f"/api/stocks/NVDA/change?date={date}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_api_change_unknown_ticker_is_404(client: FlaskClient) -> None:
    assert client.get("/api/stocks/NVDA/change").status_code == 200  # endpoint exists
    resp = client.get("/api/stocks/TSLA/change")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def day_change_element(html: str) -> tuple[str, str]:
    match = re.search(r'<(\w+)([^>]*\bid="day-change"[^>]*)>(.*?)</\1>', html, re.S)
    assert match, "no element with id=day-change"
    attrs, text = match.group(2), re.sub(r"<[^>]+>", "", match.group(3))
    return attrs, " ".join(text.split())


@pytest.mark.parametrize("ticker", list(stocks.TICKERS))
def test_ui_day_change_text_and_class(client: FlaskClient, ticker: str) -> None:
    want = expected(ticker, -1)
    attrs, text = day_change_element(client.get(f"/?ticker={ticker}").get_data(as_text=True))
    sign = "+" if want["change"] >= 0 else "-"
    assert text == f"{sign}{abs(want['change']):.2f} ({sign}{abs(want['change_pct']):.2f}%)"
    classes = re.search(r'class="([^"]*)"', attrs)
    assert classes, "day-change element has no class attribute"
    assert ("up" if sign == "+" else "down") in classes.group(1).split()

import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected(ticker: str, window: int) -> list[dict]:
    closes = [b.close for b in stocks.load_prices(ticker)]
    dates = [b.date for b in stocks.load_prices(ticker)]
    return [
        {"date": dates[i], "value": round(sum(closes[i - window + 1 : i + 1]) / window, 2)}
        for i in range(window - 1, len(closes))
    ]


def assert_series(actual: list[dict], want: list[dict]) -> None:
    assert len(actual) == len(want)
    assert [a["date"] for a in actual] == [w["date"] for w in want]
    for a, w in zip(actual, want):
        assert a["value"] == pytest.approx(w["value"], abs=0.006)


def test_function_window_20() -> None:
    assert_series(stocks.moving_average("NVDA", 20), expected("NVDA", 20))


def test_function_window_2_case_insensitive() -> None:
    assert_series(stocks.moving_average("meta", 2), expected("META", 2))


def test_function_full_length_window_has_one_value() -> None:
    n = len(stocks.load_prices("AAPL"))
    result = stocks.moving_average("AAPL", n)
    assert_series(result, expected("AAPL", n))
    assert len(result) == 1


@pytest.mark.parametrize("window", [1, 0, -3, 10_000, True])
def test_function_invalid_window(window: int) -> None:
    with pytest.raises(ValueError):
        stocks.moving_average("AAPL", window)


def test_function_unknown_ticker() -> None:
    with pytest.raises(stocks.UnknownTickerError):
        stocks.moving_average("TSLA", 5)


def test_api_default_window(client: FlaskClient) -> None:
    resp = client.get("/api/stocks/msft/sma")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["ticker"] == "MSFT"
    assert data["window"] == 20
    assert_series(data["values"], expected("MSFT", 20))


def test_api_custom_window(client: FlaskClient) -> None:
    data = client.get("/api/stocks/GOOGL/sma?window=50").get_json()
    assert data["window"] == 50
    assert_series(data["values"], expected("GOOGL", 50))


@pytest.mark.parametrize("window", ["abc", "2.5", "1", "0", "100000", ""])
def test_api_invalid_window_is_400(client: FlaskClient, window: str) -> None:
    assert client.get("/api/stocks/NVDA/sma?window=5").status_code == 200  # endpoint exists
    resp = client.get(f"/api/stocks/NVDA/sma?window={window}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_api_unknown_ticker_is_404(client: FlaskClient) -> None:
    assert client.get("/api/stocks/NVDA/sma").status_code == 200  # endpoint exists
    resp = client.get("/api/stocks/TSLA/sma")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def test_ui_has_toggle_with_label(client: FlaskClient) -> None:
    html = client.get("/").get_data(as_text=True)
    assert re.search(r'<input(?=[^>]*\btype="checkbox")(?=[^>]*\bid="sma-toggle")[^>]*>', html)
    label = re.search(r'<label[^>]*\bfor="sma-toggle"[^>]*>(.*?)</label>', html, re.S)
    assert label and "20-day SMA" in label.group(1)


def test_js_requests_sma_endpoint(client: FlaskClient) -> None:
    js = client.get("/static/app.js").get_data(as_text=True)
    assert "sma-toggle" in js
    assert "/sma" in js

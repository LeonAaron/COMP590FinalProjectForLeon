from flask.testing import FlaskClient

from stockapp.stocks import TICKERS


def test_index_renders_selector_and_chart(client: FlaskClient) -> None:
    html = client.get("/").get_data(as_text=True)
    assert 'id="ticker-select"' in html
    assert 'id="price-chart"' in html
    for ticker in TICKERS:
        assert f'value="{ticker}"' in html


def test_index_selects_requested_ticker(client: FlaskClient) -> None:
    html = client.get("/?ticker=msft").get_data(as_text=True)
    assert 'data-ticker="MSFT"' in html
    assert "Microsoft Corporation" in html


def test_index_falls_back_on_unknown_ticker(client: FlaskClient) -> None:
    resp = client.get("/?ticker=ZZZZ")
    assert resp.status_code == 200
    assert 'data-ticker="NVDA"' in resp.get_data(as_text=True)


def test_api_lists_all_stocks(client: FlaskClient) -> None:
    data = client.get("/api/stocks").get_json()
    assert [d["ticker"] for d in data] == list(TICKERS)


def test_api_returns_prices(client: FlaskClient) -> None:
    data = client.get("/api/stocks/meta").get_json()
    assert data["ticker"] == "META"
    assert set(data["prices"][0]) == {"date", "open", "high", "low", "close", "volume"}


def test_api_unknown_ticker_is_404_json(client: FlaskClient) -> None:
    resp = client.get("/api/stocks/TSLA")
    assert resp.status_code == 404
    assert "error" in resp.get_json()

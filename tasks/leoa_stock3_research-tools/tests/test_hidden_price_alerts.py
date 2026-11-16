import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks
from stockapp import create_app


def last(ticker: str) -> float:
    return stocks.load_prices(ticker)[-1].close


def post(client: FlaskClient, ticker="NVDA", direction="above", price=1.0):
    return client.post("/api/alerts", json={"ticker": ticker, "direction": direction, "price": price})


def test_create_returns_201_with_fields(client: FlaskClient) -> None:
    resp = post(client, "nvda", "above", 1)
    assert resp.status_code == 201
    assert resp.get_json() == {"id": 1, "ticker": "NVDA", "direction": "above", "price": 1.0, "triggered": True}


def test_triggered_rules(client: FlaskClient) -> None:
    close = last("MSFT")
    cases = [("above", close, True), ("above", close + 0.01, False), ("below", close, True), ("below", close - 0.01, False)]
    for direction, price, want in cases:
        assert post(client, "MSFT", direction, price).get_json()["triggered"] is want, (direction, price)


def test_ids_increment_and_are_not_reused(client: FlaskClient) -> None:
    assert post(client).get_json()["id"] == 1
    assert post(client).get_json()["id"] == 2
    assert client.delete("/api/alerts/2").status_code == 204
    assert post(client).get_json()["id"] == 3


def test_list_in_order_and_filter(client: FlaskClient) -> None:
    post(client, "AAPL", "below", 10)
    post(client, "NVDA", "above", 10)
    post(client, "aapl", "above", 10_000)
    alerts = client.get("/api/alerts").get_json()["alerts"]
    assert [(a["id"], a["ticker"]) for a in alerts] == [(1, "AAPL"), (2, "NVDA"), (3, "AAPL")]
    filtered = client.get("/api/alerts?ticker=aapl").get_json()["alerts"]
    assert [a["id"] for a in filtered] == [1, 3]
    assert [a["triggered"] for a in filtered] == [False, False]


def test_filter_unknown_ticker_is_400(client: FlaskClient) -> None:
    assert client.get("/api/alerts").status_code == 200  # endpoint exists
    resp = client.get("/api/alerts?ticker=TSLA")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_state_is_per_app_instance() -> None:
    first, second = create_app().test_client(), create_app().test_client()
    post(first, "META", "above", 1)
    assert len(first.get("/api/alerts").get_json()["alerts"]) == 1
    assert second.get("/api/alerts").get_json() == {"alerts": []}
    assert post(second).get_json()["id"] == 1


@pytest.mark.parametrize(
    "body",
    [
        ["NVDA"],
        {"direction": "above", "price": 5},
        {"ticker": "TSLA", "direction": "above", "price": 5},
        {"ticker": 7, "direction": "above", "price": 5},
        {"ticker": "NVDA", "direction": "ABOVE", "price": 5},
        {"ticker": "NVDA", "direction": "sideways", "price": 5},
        {"ticker": "NVDA", "direction": "above"},
        {"ticker": "NVDA", "direction": "above", "price": "5"},
        {"ticker": "NVDA", "direction": "above", "price": True},
        {"ticker": "NVDA", "direction": "above", "price": 0},
        {"ticker": "NVDA", "direction": "below", "price": -3},
    ],
)
def test_invalid_create_is_400(client: FlaskClient, body: object) -> None:
    assert post(client).status_code == 201  # endpoint exists
    resp = client.post("/api/alerts", json=body)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
    assert len(client.get("/api/alerts").get_json()["alerts"]) == 1


def test_delete(client: FlaskClient) -> None:
    post(client)
    post(client, "AAPL")
    resp = client.delete("/api/alerts/1")
    assert resp.status_code == 204
    assert resp.get_data() == b""
    assert [a["id"] for a in client.get("/api/alerts").get_json()["alerts"]] == [2]


def test_delete_missing_is_404(client: FlaskClient) -> None:
    post(client)
    assert client.delete("/api/alerts/1").status_code == 204  # endpoint exists
    resp = client.delete("/api/alerts/1")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def panel(client: FlaskClient, ticker: str) -> str:
    page = client.get(f"/?ticker={ticker}").get_data(as_text=True)
    match = re.search(r'<section[^>]*\bid="alerts"[^>]*>(.*?)</section>', page, re.S)
    assert match, "no <section id=alerts>"
    return match.group(1)


def test_ui_empty_message(client: FlaskClient) -> None:
    post(client, "AAPL")
    body = panel(client, "GOOGL")
    assert "No alerts for GOOGL" in body
    assert "alert-item" not in body


def test_ui_lists_selected_ticker_alerts(client: FlaskClient) -> None:
    post(client, "NVDA", "above", 1)
    post(client, "AAPL", "above", 1)
    post(client, "NVDA", "below", 1)
    items = re.findall(r'<li([^>]*)>(.*?)</li>', panel(client, "NVDA"), re.S)
    items = [(a, b) for a, b in items if "alert-item" in a]
    assert [re.search(r'data-alert-id="(\d+)"', a).group(1) for a, _ in items] == ["1", "3"]
    texts = [" ".join(re.sub(r"<[^>]+>", " ", b).split()) for _, b in items]
    assert "above 1.00" in texts[0] and "below 1.00" in texts[1]
    classes = [re.search(r'class="([^"]*)"', a).group(1).split() for a, _ in items]
    assert "triggered" in classes[0] and "triggered" not in classes[1]

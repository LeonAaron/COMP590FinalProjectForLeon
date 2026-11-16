import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected(tickers: list[str]) -> dict:
    closes = {t: {b.date: b.close for b in stocks.load_prices(t)} for t in tickers}
    common = sorted(set.intersection(*(set(c) for c in closes.values())))
    return {
        "tickers": tickers,
        "dates": common,
        "series": {t: [round(closes[t][d] / closes[t][common[0]] * 100, 2) for d in common] for t in tickers},
    }


def assert_compare(actual: dict, want: dict) -> None:
    assert actual["tickers"] == want["tickers"]
    assert actual["dates"] == want["dates"]
    assert list(actual["series"]) == want["tickers"]
    for t in want["tickers"]:
        assert actual["series"][t] == pytest.approx(want["series"][t], abs=0.006)


def test_function_two() -> None:
    assert_compare(stocks.compare(["nvda", "MSFT"]), expected(["NVDA", "MSFT"]))


def test_function_five_keeps_order() -> None:
    order = ["META", "AAPL", "NVDA", "GOOGL", "MSFT"]
    result = stocks.compare(order)
    assert_compare(result, expected(order))
    assert all(series[0] == 100.0 for series in result["series"].values())


@pytest.mark.parametrize(
    "tickers",
    [["NVDA"], [], ["NVDA", "nvda"], ["NVDA", "MSFT", "AAPL", "GOOGL", "META", "NVDA"]],
    ids=["one", "none", "duplicate", "six"],
)
def test_function_invalid(tickers: list[str]) -> None:
    with pytest.raises(ValueError):
        stocks.compare(tickers)


def test_function_unknown() -> None:
    with pytest.raises(stocks.UnknownTickerError):
        stocks.compare(["NVDA", "TSLA"])


def test_api(client: FlaskClient) -> None:
    resp = client.get("/api/compare?tickers=aapl,GOOGL")
    assert resp.status_code == 200
    assert_compare(resp.get_json(), expected(["AAPL", "GOOGL"]))


def test_api_whitespace_and_trailing_comma(client: FlaskClient) -> None:
    resp = client.get("/api/compare?tickers= meta , msft ,")
    assert resp.status_code == 200
    assert_compare(resp.get_json(), expected(["META", "MSFT"]))


@pytest.mark.parametrize(
    "query", ["", "tickers=", "tickers=NVDA", "tickers=NVDA,nvda", "tickers=NVDA,TSLA",
              "tickers=NVDA,MSFT,AAPL,GOOGL,META,NVDA"],
)
def test_api_invalid_is_400(client: FlaskClient, query: str) -> None:
    assert client.get("/api/compare?tickers=NVDA,MSFT").status_code == 200  # endpoint exists
    resp = client.get(f"/api/compare?{query}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def page(client: FlaskClient, query: str = "") -> str:
    resp = client.get(f"/compare{query}")
    assert resp.status_code == 200
    return resp.get_data(as_text=True)


def chart_tickers(html: str) -> str:
    match = re.search(r'<div(?=[^>]*\bid="compare-chart")[^>]*\bdata-tickers="([^"]*)"', html)
    assert match, "no compare-chart div with data-tickers"
    return match.group(1)


def test_page_with_tickers(client: FlaskClient) -> None:
    assert chart_tickers(page(client, "?tickers=msft,nvda")) == "MSFT,NVDA"


@pytest.mark.parametrize("query", ["", "?tickers=NVDA", "?tickers=NVDA,TSLA"])
def test_page_defaults_to_all(client: FlaskClient, query: str) -> None:
    assert chart_tickers(page(client, query)) == ",".join(stocks.TICKERS)


def test_page_table_last_values(client: FlaskClient) -> None:
    html = page(client, "?tickers=META,AAPL,NVDA")
    table = re.search(r'<table[^>]*\bid="compare-table"[^>]*>(.*?)</table>', html, re.S)
    assert table
    rows = re.findall(r'<tr[^>]*\bdata-ticker="([A-Z]+)"[^>]*>(.*?)</tr>', table.group(1), re.S)
    assert [t for t, _ in rows] == ["META", "AAPL", "NVDA"]
    want = expected(["META", "AAPL", "NVDA"])
    for ticker, row in rows:
        cells = [" ".join(re.sub(r"<[^>]+>", "", c).split()) for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)]
        assert cells == [ticker, f"{want['series'][ticker][-1]:.2f}"]


def test_index_links_to_compare(client: FlaskClient) -> None:
    assert re.search(r'<a[^>]*\bhref="/compare', client.get("/").get_data(as_text=True))

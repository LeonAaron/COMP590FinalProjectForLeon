import csv
import io
import re

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def expected_rows(ticker: str) -> list[list[str]]:
    bars = stocks.load_prices(ticker)
    rows = []
    for i, b in enumerate(bars):
        pct = "" if i == 0 else f"{round((b.close - bars[i - 1].close) / bars[i - 1].close * 100, 2):.2f}"
        rows.append([b.date, f"{b.open:.2f}", f"{b.high:.2f}", f"{b.low:.2f}", f"{b.close:.2f}", str(b.volume), pct])
    return rows


def parse(resp) -> list[list[str]]:
    return list(csv.reader(io.StringIO(resp.get_data(as_text=True))))


def get(client: FlaskClient, ticker: str, query: str = ""):
    resp = client.get(f"/api/stocks/{ticker}/export.csv{query}")
    assert resp.status_code == 200
    return resp


def test_content_type(client: FlaskClient) -> None:
    assert get(client, "NVDA").mimetype == "text/csv"


def test_attachment_filename(client: FlaskClient) -> None:
    disposition = get(client, "nvda").headers.get("Content-Disposition", "")
    assert disposition.startswith("attachment")
    assert re.search(r'filename="?NVDA_prices\.csv"?', disposition)


def test_header_row(client: FlaskClient) -> None:
    assert parse(get(client, "MSFT"))[0] == ["date", "open", "high", "low", "close", "volume", "change_pct"]


@pytest.mark.parametrize("ticker", ["MSFT", "META"])
def test_rows_ascending(client: FlaskClient, ticker: str) -> None:
    assert parse(get(client, ticker.lower()))[1:] == expected_rows(ticker)


def test_first_row_change_is_empty(client: FlaskClient) -> None:
    rows = parse(get(client, "AAPL"))
    assert rows[1][6] == ""
    assert rows[2][6] != ""


def test_explicit_asc(client: FlaskClient) -> None:
    assert parse(get(client, "AAPL", "?order=asc"))[1:] == expected_rows("AAPL")


def test_desc_keeps_chronological_change(client: FlaskClient) -> None:
    rows = parse(get(client, "GOOGL", "?order=desc"))
    assert rows[0][0] == "date"
    assert rows[1:] == list(reversed(expected_rows("GOOGL")))
    assert rows[-1][6] == ""


@pytest.mark.parametrize("order", ["DESC", "newest", ""])
def test_bad_order_is_400(client: FlaskClient, order: str) -> None:
    get(client, "NVDA")  # endpoint exists
    resp = client.get(f"/api/stocks/NVDA/export.csv?order={order}")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_unknown_ticker_is_404(client: FlaskClient) -> None:
    get(client, "NVDA")  # endpoint exists
    resp = client.get("/api/stocks/TSLA/export.csv")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


@pytest.mark.parametrize("ticker", ["NVDA", "GOOGL"])
def test_index_export_link(client: FlaskClient, ticker: str) -> None:
    page = client.get(f"/?ticker={ticker}").get_data(as_text=True)
    link = re.search(r'<a(?=[^>]*\bid="export-link")([^>]*)>', page)
    assert link
    assert f'href="/api/stocks/{ticker}/export.csv"' in link.group(1)
    assert re.search(r"\bdownload\b", link.group(1))

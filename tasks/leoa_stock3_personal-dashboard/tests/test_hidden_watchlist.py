import importlib
import json
import re
from pathlib import Path

import pytest
from flask.testing import FlaskClient

from stockapp.stocks import UnknownTickerError


@pytest.fixture
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "nested" / "watchlist.json"
    monkeypatch.setenv("WATCHLIST_PATH", str(path))
    return path


def wl():
    return importlib.import_module("stockapp.watchlist")


def test_missing_file_is_empty(store: Path) -> None:
    assert wl().load_watchlist() == []


def test_add_normalizes_dedupes_and_persists(store: Path) -> None:
    w = wl()
    assert w.add_to_watchlist(" nvda ") == ["NVDA"]
    assert w.add_to_watchlist("aapl") == ["NVDA", "AAPL"]
    assert w.add_to_watchlist("NVDA") == ["NVDA", "AAPL"]
    assert json.loads(store.read_text()) == ["NVDA", "AAPL"]


def test_path_is_read_at_call_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    w = wl()
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    monkeypatch.setenv("WATCHLIST_PATH", str(first))
    w.add_to_watchlist("MSFT")
    monkeypatch.setenv("WATCHLIST_PATH", str(second))
    assert w.load_watchlist() == []
    assert json.loads(first.read_text()) == ["MSFT"]


def test_add_unknown_raises(store: Path) -> None:
    with pytest.raises(UnknownTickerError):
        wl().add_to_watchlist("TSLA")


def test_remove(store: Path) -> None:
    w = wl()
    w.add_to_watchlist("NVDA")
    w.add_to_watchlist("META")
    assert w.remove_from_watchlist("nvda") == ["META"]
    with pytest.raises(KeyError):
        w.remove_from_watchlist("NVDA")


def test_api_get_empty(client: FlaskClient, store: Path) -> None:
    resp = client.get("/api/watchlist")
    assert resp.status_code == 200
    assert resp.get_json() == {"tickers": []}


def test_api_post_201_then_200(client: FlaskClient, store: Path) -> None:
    first = client.post("/api/watchlist", json={"ticker": "googl"})
    assert first.status_code == 201
    assert first.get_json() == {"tickers": ["GOOGL"]}
    again = client.post("/api/watchlist", json={"ticker": "GOOGL"})
    assert again.status_code == 200
    assert again.get_json() == {"tickers": ["GOOGL"]}
    assert client.get("/api/watchlist").get_json() == {"tickers": ["GOOGL"]}


@pytest.mark.parametrize(
    "body",
    [{"ticker": "TSLA"}, {"symbol": "NVDA"}, {"ticker": 5}, ["NVDA"]],
    ids=["unknown", "missing", "not-string", "not-object"],
)
def test_api_post_invalid_is_400(client: FlaskClient, store: Path, body: object) -> None:
    resp = client.post("/api/watchlist", json=body)
    assert resp.status_code == 400
    assert "error" in resp.get_json()
    assert client.get("/api/watchlist").get_json() == {"tickers": []}


def test_api_delete(client: FlaskClient, store: Path) -> None:
    client.post("/api/watchlist", json={"ticker": "NVDA"})
    client.post("/api/watchlist", json={"ticker": "MSFT"})
    resp = client.delete("/api/watchlist/nvda")
    assert resp.status_code == 200
    assert resp.get_json() == {"tickers": ["MSFT"]}


def test_api_delete_missing_is_404(client: FlaskClient, store: Path) -> None:
    client.post("/api/watchlist", json={"ticker": "MSFT"})
    resp = client.delete("/api/watchlist/AAPL")
    assert resp.status_code == 404
    assert "error" in resp.get_json()
    assert client.get("/api/watchlist").get_json() == {"tickers": ["MSFT"]}


def panel(html: str) -> str:
    match = re.search(r'<section[^>]*\bid="watchlist"[^>]*>(.*?)</section>', html, re.S)
    assert match, "no <section id=watchlist>"
    return match.group(1)


def test_ui_empty_message(client: FlaskClient, store: Path) -> None:
    assert "Your watchlist is empty" in panel(client.get("/").get_data(as_text=True))


def test_ui_lists_items_in_order(client: FlaskClient, store: Path) -> None:
    client.post("/api/watchlist", json={"ticker": "META"})
    client.post("/api/watchlist", json={"ticker": "AAPL"})
    body = panel(client.get("/").get_data(as_text=True))
    items = re.findall(r'<[^>]*class="[^"]*\bwatchlist-item\b[^"]*"[^>]*>', body)
    tickers = [re.search(r'data-ticker="([A-Z]+)"', tag).group(1) for tag in items]
    assert tickers == ["META", "AAPL"]
    assert "Your watchlist is empty" not in body

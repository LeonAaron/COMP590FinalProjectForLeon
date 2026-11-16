import html as htmllib
import importlib
import math
import re
import statistics

import pytest
from flask.testing import FlaskClient

import stockapp.stocks as stocks


def report_mod():
    return importlib.import_module("stockapp.report")


def expected(ticker: str) -> str:
    bars = stocks.load_prices(ticker)
    closes = [b.close for b in bars]
    logs = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    sma50 = sum(closes[-50:]) / 50
    trend = "Bullish" if closes[-1] > sma50 else "Bearish" if closes[-1] < sma50 else "Neutral"
    return (
        f"# {stocks.TICKERS[ticker]} ({ticker}) Analysis Report\n\n"
        "## Price Summary\n"
        f"- Last close: ${closes[-1]:.2f} (as of {bars[-1].date})\n"
        f"- 52-week high: ${max(b.high for b in bars):.2f}\n"
        f"- 52-week low: ${min(b.low for b in bars):.2f}\n\n"
        "## Performance\n"
        f"- 1-year return: {(closes[-1] / closes[0] - 1) * 100:+.2f}%\n"
        f"- 1-month return: {(closes[-1] / closes[-22] - 1) * 100:+.2f}%\n\n"
        "## Volatility\n"
        f"- Annualized volatility: {statistics.stdev(logs) * math.sqrt(252) * 100:.2f}%\n\n"
        "## Trend\n"
        f"- 50-day SMA: ${sma50:.2f}\n"
        f"- Trend: {trend}\n"
    )


def section(md: str, heading: str) -> str:
    match = re.search(rf"^## {heading}\n(.*?)(?=\n## |\Z)", md, re.S | re.M)
    assert match, f"missing section {heading}"
    return match.group(1).strip()


@pytest.mark.parametrize("ticker", list(stocks.TICKERS))
def test_full_report_exact(ticker: str) -> None:
    assert report_mod().generate_report(ticker.lower()) == expected(ticker)


@pytest.mark.parametrize("heading", ["Price Summary", "Performance", "Volatility", "Trend"])
def test_sections_nvda(heading: str) -> None:
    got, want = report_mod().generate_report("NVDA"), expected("NVDA")
    assert section(got, heading) == section(want, heading)


def test_title_line() -> None:
    first = report_mod().generate_report("META").splitlines()[0]
    assert first == "# Meta Platforms, Inc. (META) Analysis Report"


def test_unknown_ticker() -> None:
    with pytest.raises(stocks.UnknownTickerError):
        report_mod().generate_report("TSLA")


def test_api_markdown(client: FlaskClient) -> None:
    resp = client.get("/api/stocks/msft/report.md")
    assert resp.status_code == 200
    assert resp.mimetype == "text/markdown"
    assert resp.get_data(as_text=True) == expected("MSFT")


def test_api_markdown_unknown_is_404(client: FlaskClient) -> None:
    assert client.get("/api/stocks/MSFT/report.md").status_code == 200  # endpoint exists
    resp = client.get("/api/stocks/TSLA/report.md")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


def article(client: FlaskClient, ticker: str) -> str:
    resp = client.get(f"/report/{ticker}")
    assert resp.status_code == 200
    match = re.search(r'<article[^>]*\bid="report"[^>]*>(.*?)</article>', resp.get_data(as_text=True), re.S)
    assert match, "no <article id=report>"
    return match.group(1)


def text_of(tag: str, fragment: str) -> list[str]:
    return [htmllib.unescape(" ".join(re.sub(r"<[^>]+>", "", m).split())) for m in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", fragment, re.S)]


def test_html_headings(client: FlaskClient) -> None:
    body = article(client, "aapl")
    assert text_of("h1", body) == ["Apple Inc. (AAPL) Analysis Report"]
    assert text_of("h2", body) == ["Price Summary", "Performance", "Volatility", "Trend"]


def test_html_bullets(client: FlaskClient) -> None:
    want = [line[2:] for line in expected("GOOGL").splitlines() if line.startswith("- ")]
    assert text_of("li", article(client, "GOOGL")) == want


def test_html_is_escaped(client: FlaskClient) -> None:
    raw = client.get("/report/GOOGL").get_data(as_text=True)
    assert "Alphabet Inc. (Google)" in raw
    assert "<ul" in raw


def test_html_unknown_is_404(client: FlaskClient) -> None:
    assert client.get("/report/NVDA").status_code == 200  # page exists
    assert client.get("/report/TSLA").status_code == 404


@pytest.mark.parametrize("ticker", ["NVDA", "META"])
def test_index_report_link(client: FlaskClient, ticker: str) -> None:
    page = client.get(f"/?ticker={ticker}").get_data(as_text=True)
    link = re.search(r'<a(?=[^>]*\bid="report-link")[^>]*\bhref="([^"]+)"', page)
    assert link and link.group(1) == f"/report/{ticker}"

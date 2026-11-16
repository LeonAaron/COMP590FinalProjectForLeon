import pytest

from stockapp.stocks import TICKERS, UnknownTickerError, latest_bar, load_prices, normalize_ticker


@pytest.mark.parametrize("ticker", list(TICKERS))
def test_every_ticker_has_a_year_of_sorted_valid_bars(ticker: str) -> None:
    bars = load_prices(ticker)
    assert len(bars) >= 200
    dates = [b.date for b in bars]
    assert dates == sorted(dates)
    assert len(set(dates)) == len(dates)
    for b in bars:
        assert b.low <= min(b.open, b.close) <= max(b.open, b.close) <= b.high
        assert b.volume >= 0


def test_normalize_ticker_is_case_and_space_insensitive() -> None:
    assert normalize_ticker(" nvda ") == "NVDA"


def test_unknown_ticker_raises() -> None:
    with pytest.raises(UnknownTickerError):
        load_prices("TSLA")


def test_latest_bar_is_last_date() -> None:
    assert latest_bar("AAPL") == load_prices("AAPL")[-1]

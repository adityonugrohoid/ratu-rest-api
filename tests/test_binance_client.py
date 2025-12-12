"""
Tests for the Binance client module.
"""

from rest_api.binance_client import BinanceClient, Ticker24h, TickerPrice


def test_binance_client_creation():
    """Test BinanceClient can be created."""
    client = BinanceClient()
    assert client.base_url is not None
    client.close()


def test_binance_client_context_manager():
    """Test BinanceClient context manager."""
    with BinanceClient() as client:
        assert client.base_url is not None


def test_ticker_price_dataclass():
    """Test TickerPrice dataclass."""
    ticker = TickerPrice(symbol="ETHUSDT", price=3500.50)
    assert ticker.symbol == "ETHUSDT"
    assert ticker.price == 3500.50


def test_ticker_24h_dataclass():
    """Test Ticker24h dataclass."""
    ticker = Ticker24h(
        symbol="ETHUSDT",
        price_change=50.0,
        price_change_percent=1.5,
        weighted_avg_price=3480.0,
        prev_close_price=3450.0,
        last_price=3500.0,
        bid_price=3499.0,
        ask_price=3501.0,
        open_price=3450.0,
        high_price=3550.0,
        low_price=3400.0,
        volume=10000.0,
        quote_volume=35000000.0,
        open_time=1699999999000,
        close_time=1700099999000,
        trade_count=50000,
    )
    assert ticker.symbol == "ETHUSDT"
    assert ticker.price_change_percent == 1.5

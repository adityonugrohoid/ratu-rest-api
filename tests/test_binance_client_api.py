"""
Tests for BinanceClient API methods with mocked HTTP responses.

These tests verify API method logic without making real network requests.
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from rest_api.binance_client import (
    BinanceClient,
    Kline,
    OrderBookDepth,
    RecentTrade,
    Ticker24h,
    TickerPrice,
)


class TestBinanceClientPing:
    """Tests for ping method."""

    def test_ping_success(self):
        """Test ping returns True on success."""
        with patch.object(BinanceClient, "_get", return_value={}):
            client = BinanceClient()
            result = client.ping()
            assert result is True
            client.close()

    def test_ping_failure(self):
        """Test ping returns False on connection error."""
        with patch.object(
            BinanceClient, "_get", side_effect=httpx.ConnectError("Connection failed")
        ):
            client = BinanceClient()
            result = client.ping()
            assert result is False
            client.close()


class TestBinanceClientTickerPrice:
    """Tests for get_ticker_price method."""

    def test_get_ticker_price_mocked(self):
        """Test get_ticker_price with mocked response."""
        mock_response = {"symbol": "ETHUSDT", "price": "3500.50"}

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_ticker_price("ETHUSDT")

            assert isinstance(result, TickerPrice)
            assert result.symbol == "ETHUSDT"
            assert result.price == 3500.50
            client.close()


class TestBinanceClientTicker24h:
    """Tests for get_ticker_24h method."""

    def test_get_ticker_24h_mocked(self):
        """Test get_ticker_24h with mocked response."""
        mock_response = {
            "symbol": "ETHUSDT",
            "priceChange": "50.00",
            "priceChangePercent": "1.50",
            "weightedAvgPrice": "3480.00",
            "prevClosePrice": "3450.00",
            "lastPrice": "3500.00",
            "bidPrice": "3499.00",
            "askPrice": "3501.00",
            "openPrice": "3450.00",
            "highPrice": "3550.00",
            "lowPrice": "3400.00",
            "volume": "10000.00",
            "quoteVolume": "35000000.00",
            "openTime": 1699999999000,
            "closeTime": 1700099999000,
            "count": 50000,
        }

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_ticker_24h("ETHUSDT")

            assert isinstance(result, Ticker24h)
            assert result.symbol == "ETHUSDT"
            assert result.price_change == 50.0
            assert result.price_change_percent == 1.5
            assert result.last_price == 3500.0
            assert result.trade_count == 50000
            client.close()


class TestBinanceClientOrderBook:
    """Tests for get_order_book method."""

    def test_get_order_book_mocked(self):
        """Test get_order_book with mocked response."""
        mock_response = {
            "lastUpdateId": 12345678,
            "bids": [["3499.00", "1.5"], ["3498.00", "2.0"]],
            "asks": [["3501.00", "1.0"], ["3502.00", "2.5"]],
        }

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_order_book("ETHUSDT", limit=20)

            assert isinstance(result, OrderBookDepth)
            assert result.symbol == "ETHUSDT"
            assert result.last_update_id == 12345678
            assert len(result.bids) == 2
            assert len(result.asks) == 2
            assert result.bids[0] == (3499.0, 1.5)
            assert result.asks[0] == (3501.0, 1.0)
            client.close()


class TestBinanceClientRecentTrades:
    """Tests for get_recent_trades method."""

    def test_get_recent_trades_mocked(self):
        """Test get_recent_trades with mocked response."""
        mock_response = [
            {
                "id": 123456,
                "price": "3500.00",
                "qty": "0.5",
                "quoteQty": "1750.00",
                "time": 1700000000000,
                "isBuyerMaker": False,
            },
            {
                "id": 123457,
                "price": "3501.00",
                "qty": "1.0",
                "quoteQty": "3501.00",
                "time": 1700000001000,
                "isBuyerMaker": True,
            },
        ]

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_recent_trades("ETHUSDT", limit=10)

            assert isinstance(result, list)
            assert len(result) == 2
            assert isinstance(result[0], RecentTrade)
            assert result[0].trade_id == 123456
            assert result[0].price == 3500.0
            assert result[0].is_buyer_maker is False
            client.close()


class TestBinanceClientKlines:
    """Tests for get_klines method."""

    def test_get_klines_mocked(self):
        """Test get_klines with mocked response."""
        mock_response = [
            [
                1700000000000,  # open_time
                "3400.00",  # open
                "3550.00",  # high
                "3380.00",  # low
                "3500.00",  # close
                "1000.00",  # volume
                1700003600000,  # close_time
                "3500000.00",  # quote_volume
                5000,  # trade_count
                "600.00",  # taker_buy_volume
                "2100000.00",  # taker_buy_quote_volume
                "0",  # ignore
            ]
        ]

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_klines("ETHUSDT", interval="1h", limit=1)

            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], Kline)
            assert result[0].open == 3400.0
            assert result[0].high == 3550.0
            assert result[0].close == 3500.0
            assert result[0].trade_count == 5000
            client.close()


class TestBinanceClientErrorHandling:
    """Tests for error handling."""

    def test_http_status_error(self):
        """Test that HTTP errors are raised properly."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad Request", request=MagicMock(), response=mock_response
        )

        with patch.object(BinanceClient, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.get.return_value = mock_response
            mock_get_client.return_value = mock_client

            client = BinanceClient()
            with pytest.raises(httpx.HTTPStatusError):
                client._get("/api/v3/ticker/price", {"symbol": "INVALID"})
            client.close()

    def test_get_avg_price_mocked(self):
        """Test get_avg_price with mocked response."""
        mock_response = {"mins": 5, "price": "3495.50", "closeTime": 1700000000000}

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_avg_price("ETHUSDT")

            assert result == 3495.5
            client.close()

    def test_get_book_ticker_mocked(self):
        """Test get_book_ticker with mocked response."""
        mock_response = {
            "symbol": "ETHUSDT",
            "bidPrice": "3499.00",
            "bidQty": "10.5",
            "askPrice": "3501.00",
            "askQty": "8.2",
        }

        with patch.object(BinanceClient, "_get", return_value=mock_response):
            client = BinanceClient()
            result = client.get_book_ticker("ETHUSDT")

            assert result["symbol"] == "ETHUSDT"
            assert result["bid_price"] == 3499.0
            assert result["ask_price"] == 3501.0
            client.close()

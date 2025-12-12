"""
Binance public REST API client.

Provides methods for querying public market data endpoints.
No authentication required for these endpoints.

API Documentation: https://binance-docs.github.io/apidocs/spot/en/
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from rest_api.config import BINANCE_BASE_URL, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)


@dataclass
class TickerPrice:
    """Current price for a symbol."""

    symbol: str
    price: float


@dataclass
class Ticker24h:
    """24-hour price change statistics."""

    symbol: str
    price_change: float
    price_change_percent: float
    weighted_avg_price: float
    prev_close_price: float
    last_price: float
    bid_price: float
    ask_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: int
    close_time: int
    trade_count: int


@dataclass
class OrderBookDepth:
    """Order book depth data."""

    symbol: str
    bids: list[tuple[float, float]]  # (price, quantity)
    asks: list[tuple[float, float]]  # (price, quantity)
    last_update_id: int


@dataclass
class RecentTrade:
    """Recent trade data."""

    trade_id: int
    price: float
    qty: float
    quote_qty: float
    time: int
    is_buyer_maker: bool


@dataclass
class Kline:
    """Candlestick/Kline data."""

    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_volume: float
    trade_count: int
    taker_buy_volume: float
    taker_buy_quote_volume: float


class BinanceClient:
    """
    Client for Binance public REST API.

    All endpoints are public and require no authentication.
    """

    def __init__(self, base_url: Optional[str] = None):
        """Initialize the Binance client."""
        self.base_url = base_url or BINANCE_BASE_URL
        self._client: Optional[httpx.Client] = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT,
            )
        return self._client

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Any:
        """Make a GET request to the API."""
        client = self._get_client()
        response = client.get(endpoint, params=params)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Market Data Endpoints
    # =========================================================================

    def ping(self) -> bool:
        """Test connectivity to the API."""
        try:
            self._get("/api/v3/ping")
            return True
        except Exception:
            return False

    def get_server_time(self) -> int:
        """Get server time in milliseconds."""
        data = self._get("/api/v3/time")
        return data["serverTime"]

    def get_exchange_info(self, symbol: Optional[str] = None) -> dict:
        """
        Get exchange trading rules and symbol information.

        Args:
            symbol: Optional symbol to filter (e.g., 'ETHUSDT')
        """
        params = {"symbol": symbol} if symbol else None
        return self._get("/api/v3/exchangeInfo", params)

    def get_ticker_price(self, symbol: str) -> TickerPrice:
        """
        Get current price for a symbol.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
        """
        data = self._get("/api/v3/ticker/price", {"symbol": symbol})
        return TickerPrice(
            symbol=data["symbol"],
            price=float(data["price"]),
        )

    def get_ticker_24h(self, symbol: str) -> Ticker24h:
        """
        Get 24-hour price change statistics.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
        """
        data = self._get("/api/v3/ticker/24hr", {"symbol": symbol})
        return Ticker24h(
            symbol=data["symbol"],
            price_change=float(data["priceChange"]),
            price_change_percent=float(data["priceChangePercent"]),
            weighted_avg_price=float(data["weightedAvgPrice"]),
            prev_close_price=float(data["prevClosePrice"]),
            last_price=float(data["lastPrice"]),
            bid_price=float(data["bidPrice"]),
            ask_price=float(data["askPrice"]),
            open_price=float(data["openPrice"]),
            high_price=float(data["highPrice"]),
            low_price=float(data["lowPrice"]),
            volume=float(data["volume"]),
            quote_volume=float(data["quoteVolume"]),
            open_time=data["openTime"],
            close_time=data["closeTime"],
            trade_count=data["count"],
        )

    def get_order_book(self, symbol: str, limit: int = 20) -> OrderBookDepth:
        """
        Get order book depth.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000, 5000)
        """
        data = self._get("/api/v3/depth", {"symbol": symbol, "limit": limit})
        return OrderBookDepth(
            symbol=symbol,
            bids=[(float(p), float(q)) for p, q in data["bids"]],
            asks=[(float(p), float(q)) for p, q in data["asks"]],
            last_update_id=data["lastUpdateId"],
        )

    def get_recent_trades(self, symbol: str, limit: int = 100) -> list[RecentTrade]:
        """
        Get recent trades.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
            limit: Number of trades (max 1000)
        """
        data = self._get("/api/v3/trades", {"symbol": symbol, "limit": limit})
        return [
            RecentTrade(
                trade_id=t["id"],
                price=float(t["price"]),
                qty=float(t["qty"]),
                quote_qty=float(t["quoteQty"]),
                time=t["time"],
                is_buyer_maker=t["isBuyerMaker"],
            )
            for t in data
        ]

    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> list[Kline]:
        """
        Get candlestick/kline data.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of klines (max 1000)
        """
        data = self._get(
            "/api/v3/klines",
            {"symbol": symbol, "interval": interval, "limit": limit},
        )
        return [
            Kline(
                open_time=k[0],
                open=float(k[1]),
                high=float(k[2]),
                low=float(k[3]),
                close=float(k[4]),
                volume=float(k[5]),
                close_time=k[6],
                quote_volume=float(k[7]),
                trade_count=k[8],
                taker_buy_volume=float(k[9]),
                taker_buy_quote_volume=float(k[10]),
            )
            for k in data
        ]

    def get_avg_price(self, symbol: str) -> float:
        """
        Get current average price (5-minute window).

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
        """
        data = self._get("/api/v3/avgPrice", {"symbol": symbol})
        return float(data["price"])

    def get_book_ticker(self, symbol: str) -> dict:
        """
        Get best bid/ask price and quantity.

        Args:
            symbol: Trading pair (e.g., 'ETHUSDT')
        """
        data = self._get("/api/v3/ticker/bookTicker", {"symbol": symbol})
        return {
            "symbol": data["symbol"],
            "bid_price": float(data["bidPrice"]),
            "bid_qty": float(data["bidQty"]),
            "ask_price": float(data["askPrice"]),
            "ask_qty": float(data["askQty"]),
        }

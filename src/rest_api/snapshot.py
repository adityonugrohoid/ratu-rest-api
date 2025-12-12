"""
Market snapshot module.

Creates comprehensive market analytics snapshots for a symbol.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from rest_api.binance_client import BinanceClient
from rest_api.config import SNAPSHOT_DIR

logger = logging.getLogger(__name__)


def create_market_snapshot(
    symbol: str,
    client: Optional[BinanceClient] = None,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    Create a comprehensive market snapshot for a symbol.

    Collects:
    - Current price and 24h statistics
    - Order book depth (top 20 levels)
    - Recent trades (last 100)
    - Kline data (1h, 4h, 1d intervals)
    - Book ticker (best bid/ask)

    Args:
        symbol: Trading pair (e.g., 'ETHUSDT')
        client: Optional BinanceClient instance
        output_dir: Output directory for snapshot

    Returns:
        Complete snapshot dictionary
    """
    should_close = False
    if client is None:
        client = BinanceClient()
        should_close = True

    output_dir = output_dir or SNAPSHOT_DIR

    try:
        logger.info(f"Creating market snapshot for {symbol}")

        # Collect all data
        ticker_price = client.get_ticker_price(symbol)
        ticker_24h = client.get_ticker_24h(symbol)
        order_book = client.get_order_book(symbol, limit=20)
        recent_trades = client.get_recent_trades(symbol, limit=100)
        avg_price = client.get_avg_price(symbol)
        book_ticker = client.get_book_ticker(symbol)

        # Get multiple timeframe klines
        klines_1h = client.get_klines(symbol, "1h", limit=24)  # Last 24 hours
        klines_4h = client.get_klines(symbol, "4h", limit=42)  # Last 7 days
        klines_1d = client.get_klines(symbol, "1d", limit=30)  # Last 30 days

        # Calculate additional analytics
        trades_buy = sum(1 for t in recent_trades if not t.is_buyer_maker)
        trades_sell = sum(1 for t in recent_trades if t.is_buyer_maker)
        buy_sell_ratio = trades_buy / trades_sell if trades_sell > 0 else 0

        total_bid_depth = sum(q for _, q in order_book.bids)
        total_ask_depth = sum(q for _, q in order_book.asks)
        bid_ask_ratio = total_bid_depth / total_ask_depth if total_ask_depth > 0 else 0

        spread = order_book.asks[0][0] - order_book.bids[0][0] if order_book.asks and order_book.bids else 0
        spread_percent = (spread / order_book.bids[0][0] * 100) if order_book.bids else 0

        # Build snapshot
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "summary": {
                "price": ticker_price.price,
                "avg_price_5m": avg_price,
                "price_change_24h": ticker_24h.price_change,
                "price_change_percent_24h": ticker_24h.price_change_percent,
                "high_24h": ticker_24h.high_price,
                "low_24h": ticker_24h.low_price,
                "volume_24h": ticker_24h.volume,
                "quote_volume_24h": ticker_24h.quote_volume,
                "trade_count_24h": ticker_24h.trade_count,
            },
            "book_ticker": book_ticker,
            "spread": {
                "absolute": spread,
                "percent": spread_percent,
            },
            "depth_analysis": {
                "total_bid_depth": total_bid_depth,
                "total_ask_depth": total_ask_depth,
                "bid_ask_ratio": bid_ask_ratio,
                "top_bids": order_book.bids[:5],
                "top_asks": order_book.asks[:5],
            },
            "trade_analysis": {
                "total_trades": len(recent_trades),
                "buy_trades": trades_buy,
                "sell_trades": trades_sell,
                "buy_sell_ratio": buy_sell_ratio,
                "avg_trade_size": sum(t.qty for t in recent_trades) / len(recent_trades) if recent_trades else 0,
            },
            "klines": {
                "1h": [asdict(k) for k in klines_1h[-6:]],  # Last 6 hours
                "4h": [asdict(k) for k in klines_4h[-6:]],  # Last 24 hours
                "1d": [asdict(k) for k in klines_1d[-7:]],  # Last 7 days
            },
        }

        # Save snapshot
        save_snapshot(snapshot, symbol, output_dir)

        return snapshot

    finally:
        if should_close:
            client.close()


def save_snapshot(data: dict, symbol: str, output_dir: Path) -> Path:
    """Save snapshot to JSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = output_dir / f"{symbol.lower()}_{timestamp}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Snapshot saved: {filename}")
    return filename


def load_snapshot(filepath: Path) -> dict:
    """Load snapshot from JSON file."""
    with open(filepath) as f:
        return json.load(f)

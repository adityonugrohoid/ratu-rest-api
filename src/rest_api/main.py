"""
Main entry point for Market Snapshot.

Creates comprehensive market analytics snapshots using Binance public API.
No authentication required.

Usage:
  market-snapshot <symbol>        Create snapshot (e.g., ETHUSDT)
  market-snapshot <symbol> info   Show basic info only
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from rest_api.binance_client import BinanceClient
from rest_api.config import LOG_FILE, LOG_LEVEL
from rest_api.snapshot import create_market_snapshot


def setup_logging():
    """Configure logging for the application."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),
        ],
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def print_header(symbol: str, mode: str = "snapshot"):
    """Print command header."""
    print()
    print("=" * 80)
    print(f"  MARKET SNAPSHOT - {symbol}")
    print("=" * 80)
    print()
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Mode: {mode}")
    print()
    print("-" * 80)


def print_footer():
    """Print command footer."""
    print("-" * 80)
    print(f"  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def cmd_info(symbol: str):
    """Show basic market info for a symbol."""
    print_header(symbol, "info")

    with BinanceClient() as client:
        # Check connectivity
        if not client.ping():
            print("  Error: Cannot connect to Binance API")
            return

        ticker = client.get_ticker_24h(symbol)
        book = client.get_book_ticker(symbol)

        print(f"  Symbol: {symbol}")
        print()
        print(f"  Price: ${ticker.last_price:,.2f}")
        print(f"  24h Change: {ticker.price_change:+,.2f} ({ticker.price_change_percent:+.2f}%)")
        print(f"  24h High: ${ticker.high_price:,.2f}")
        print(f"  24h Low: ${ticker.low_price:,.2f}")
        print(f"  24h Volume: {ticker.volume:,.2f}")
        print(f"  24h Trades: {ticker.trade_count:,}")
        print()
        print(f"  Best Bid: ${book['bid_price']:,.2f} ({book['bid_qty']:,.4f})")
        print(f"  Best Ask: ${book['ask_price']:,.2f} ({book['ask_qty']:,.4f})")
        spread = book['ask_price'] - book['bid_price']
        print(f"  Spread: ${spread:,.4f} ({spread / book['bid_price'] * 100:.4f}%)")

    print_footer()


def cmd_snapshot(symbol: str):
    """Create comprehensive market snapshot."""
    print_header(symbol, "snapshot")

    with BinanceClient() as client:
        # Check connectivity
        if not client.ping():
            print("  Error: Cannot connect to Binance API")
            return

        print(f"  Collecting data for {symbol}...")
        print()

        snapshot = create_market_snapshot(symbol, client)

        # Display summary
        s = snapshot["summary"]
        print(f"  Symbol: {symbol}")
        print(f"  Price: ${s['price']:,.2f}")
        print(f"  24h Change: {s['price_change_24h']:+,.2f} ({s['price_change_percent_24h']:+.2f}%)")
        print(f"  24h Range: ${s['low_24h']:,.2f} - ${s['high_24h']:,.2f}")
        print(f"  24h Volume: {s['volume_24h']:,.2f} {symbol[:-4]}")
        print(f"  24h Quote Volume: ${s['quote_volume_24h']:,.2f}")
        print(f"  24h Trades: {s['trade_count_24h']:,}")
        print()

        # Depth analysis
        d = snapshot["depth_analysis"]
        print("  Order Book Depth (top 20 levels):")
        print(f"    Total Bid Depth: {d['total_bid_depth']:,.4f}")
        print(f"    Total Ask Depth: {d['total_ask_depth']:,.4f}")
        print(f"    Bid/Ask Ratio: {d['bid_ask_ratio']:.2f}")
        print()

        # Trade analysis
        t = snapshot["trade_analysis"]
        print("  Recent Trade Analysis (last 100):")
        print(f"    Buy Trades: {t['buy_trades']} ({t['buy_trades']/t['total_trades']*100:.1f}%)")
        print(f"    Sell Trades: {t['sell_trades']} ({t['sell_trades']/t['total_trades']*100:.1f}%)")
        print(f"    Buy/Sell Ratio: {t['buy_sell_ratio']:.2f}")
        print(f"    Avg Trade Size: {t['avg_trade_size']:.4f}")
        print()

        # Spread
        sp = snapshot["spread"]
        print(f"  Spread: ${sp['absolute']:.4f} ({sp['percent']:.4f}%)")
        print()

        print(f"  Snapshot saved to: snapshots/{symbol.lower()}_*.json")

    print_footer()


def print_help():
    """Print usage help."""
    print("""
Market Snapshot - Binance Public Market Data Analytics

Usage:
  market-snapshot <symbol>        Create comprehensive snapshot
  market-snapshot <symbol> info   Show basic info only

Examples:
  market-snapshot ETHUSDT
  market-snapshot BTCUSDT info
  market-snapshot BNBUSDT

Supported: Any Binance trading pair (e.g., ETHUSDT, BTCUSDT, SOLUSDT)
""")


def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    if len(sys.argv) < 2:
        print_help()
        return

    symbol = sys.argv[1].upper()

    if symbol in ["HELP", "-H", "--HELP"]:
        print_help()
        return

    mode = sys.argv[2].lower() if len(sys.argv) > 2 else "snapshot"

    logger.info(f"Running {mode} for {symbol}")

    try:
        if mode == "info":
            cmd_info(symbol)
        else:
            cmd_snapshot(symbol)

    except Exception as e:
        logger.error(f"Command failed: {e}")
        print(f"\n  Error: {e}")
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()

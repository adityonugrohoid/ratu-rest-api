<div align="center">

# RATU REST API

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Binance market snapshot client: price, depth, trade flow, and multi-timeframe klines via public REST API**

[Getting Started](#getting-started) | [Usage](#usage) | [Architecture](#architecture)

</div>

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Architectural Decisions](#architectural-decisions)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Related Projects](#related-projects)
- [License](#license)
- [Author](#author)

## Features

- **Single-call market snapshot** - combines 7 Binance public endpoints (price, 24hr stats, depth, trades, klines x 3 timeframes, bookTicker, avgPrice) into one structured output
- **Order-book depth analysis** - top-20 bid/ask depth with bid/ask ratio and spread
- **Recent trade flow** - buy/sell breakdown across the last 100 trades
- **Multi-timeframe klines** - 1h / 4h / 1d candles for intraday to daily context
- **No auth required** - uses only public endpoints, no API key needed
- **JSON snapshot files** - timestamped `snapshots/<symbol>_<ts>.json` for offline analysis

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Package manager | `uv` |
| HTTP client | `httpx` (sync, connection-pooled) |
| Data source | Binance Public REST API (`api.binance.com/api/v3/*`) |
| Models | `dataclass` response types |
| Output | JSON snapshots + console |
| Tests | `pytest`, `pytest-asyncio` |

## Architecture

```mermaid
graph TD
    subgraph CLI
        MAIN["main.py<br/>market-snapshot"]
    end

    subgraph Core
        SNAP["snapshot.py<br/>snapshot builder"]
        CLIENT["BinanceClient<br/>binance_client.py"]
    end

    subgraph "Binance Public REST API"
        PRICE["/ticker/price"]
        STATS["/ticker/24hr"]
        DEPTH["/depth"]
        TRADES["/trades"]
        KLINES["/klines (1h/4h/1d)"]
        AVG["/avgPrice"]
        BOOK["/ticker/bookTicker"]
    end

    subgraph Output
        JSON[("snapshots/*.json")]
        CONSOLE["Console summary"]
    end

    MAIN --> SNAP
    SNAP --> CLIENT
    CLIENT --> PRICE
    CLIENT --> STATS
    CLIENT --> DEPTH
    CLIENT --> TRADES
    CLIENT --> KLINES
    CLIENT --> AVG
    CLIENT --> BOOK
    SNAP --> JSON
    MAIN --> CONSOLE

    style MAIN fill:#0f3460,color:#fff
    style SNAP fill:#533483,color:#fff
    style CLIENT fill:#16213e,color:#fff
    style PRICE fill:#16213e,color:#fff
    style STATS fill:#16213e,color:#fff
    style DEPTH fill:#16213e,color:#fff
    style TRADES fill:#16213e,color:#fff
    style KLINES fill:#16213e,color:#fff
    style AVG fill:#16213e,color:#fff
    style BOOK fill:#16213e,color:#fff
    style JSON fill:#0f3460,color:#fff
    style CONSOLE fill:#0f3460,color:#fff
```

## Getting Started

### Prerequisites

- Python 3.10+
- `uv` - see [install instructions](https://docs.astral.sh/uv/getting-started/installation/)
- No API key - Binance public endpoints are unauthenticated

### Installation

```bash
git clone https://github.com/adityonugrohoid/ratu-rest-api.git
cd ratu-rest-api
uv sync
```

### Configuration

```bash
cp .env.example .env
```

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `LOG_LEVEL` | No | `INFO` | Python logging level |

## Usage

```bash
# Full snapshot: all 7 endpoints, console + JSON file
uv run market-snapshot ETHUSDT

# Basic info only: 24hr ticker + price, no file written
uv run market-snapshot ETHUSDT info

# Any USDT pair
uv run market-snapshot BTCUSDT
uv run market-snapshot SOLUSDT
```

## How It Works

### 1. Snapshot pipeline

`snapshot.py` walks `BinanceClient`'s seven public endpoints in sequence on the same connection pool, parses each response into a typed dataclass, then assembles the combined result:

| Section | Source endpoint(s) |
|---------|--------------------|
| Summary | `/ticker/24hr`, `/ticker/price`, `/avgPrice` |
| Order book | `/depth?limit=20` |
| Trade flow | `/trades?limit=100` |
| Klines | `/klines` x `1h`, `4h`, `1d` |
| Spread | `/ticker/bookTicker` |

### 2. Order-book depth aggregation

Sums `qty` across the top-20 bids and top-20 asks separately, then computes `bid/ask ratio` and absolute `spread = best_ask - best_bid`. The ratio is a directional bias indicator: values above 1 mean more depth supporting the price than resisting it.

### 3. Trade-flow classification

For the last 100 trades, splits by Binance's `isBuyerMaker` flag:

- `isBuyerMaker == false` - market buy (taker bought)
- `isBuyerMaker == true` - market sell (taker sold)

Reports both counts and a buy/sell ratio.

### 4. Snapshot file output

Snapshots write to `snapshots/<symbol>_<timestamp>.json` with full sub-section payloads, suited for offline backtesting, dashboards, or comparing two timestamps.

## Architectural Decisions

### 1. Public endpoints only

**Decision:** Use exclusively unauthenticated Binance endpoints; no API-key support.

**Reasoning:** This client targets market-analytics snapshots, not order placement. Removing auth removes a class of secret-handling bugs and lets the repo run end-to-end in CI without credential setup. Trade-off: no access to account state or placed orders, which is out of scope.

### 2. Sequential calls on a pooled client

**Decision:** Walk the seven endpoints one after another on a single `httpx.Client`, not in parallel via async.

**Reasoning:** Total latency is dominated by Binance's per-endpoint response time (~50-100ms each), not Python's HTTP overhead. Pool reuse already eliminates TCP handshake cost. Sequential code is easier to read and debug; async would save roughly 100ms at the cost of materially more complexity.

### 3. Dataclass response models, not raw dicts

**Decision:** Every endpoint response is parsed into a typed dataclass before downstream code touches it.

**Reasoning:** The Binance API returns numbers as strings. Rolling that conversion into the dataclass `__post_init__` means downstream analytics never encounter string-vs-float arithmetic errors. Cost is ~50 lines of dataclass plumbing per response shape.

## Project Structure

```
ratu-rest-api/
├── src/rest_api/
│   ├── main.py             # CLI: market-snapshot entrypoint
│   ├── config.py           # API base URL, log level, output paths
│   ├── binance_client.py   # BinanceClient (httpx) + dataclass response types
│   └── snapshot.py         # 7-endpoint pipeline + JSON writer
├── tests/
│   ├── conftest.py
│   ├── test_config.py              # Config defaults, base URL
│   ├── test_binance_client.py      # Client unit tests: request building, dataclass parsing
│   └── test_binance_client_api.py  # Live API contract checks against Binance public endpoints
├── snapshots/              # JSON output (gitignored)
├── .env.example
├── pyproject.toml          # uv-managed, Python 3.10+
└── uv.lock
```

## Testing

```bash
uv run pytest tests/ -v
```

| Module | Coverage |
|--------|----------|
| `test_config.py` | Config defaults, base URL |
| `test_binance_client.py` | Client unit tests: request building, dataclass parsing |
| `test_binance_client_api.py` | Live API contract checks against Binance public endpoints |

## License

This project is licensed under the [MIT License](LICENSE).

## Author

**Adityo Nugroho** ([@adityonugrohoid](https://github.com/adityonugrohoid))

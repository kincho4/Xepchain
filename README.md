# Cryptocurrency Payment Processor - NEA project

A multi-chain cryptocurrency payment processor built with Python and Flask, supporting 8+ blockchain networks with real-time transaction detection.

## Features

- Multi-chain support for major cryptocurrencies
- Real-time transaction detection via Blockchair API
- Confirmation tracking per blockchain
- RESTful API for creating and monitoring deposits
- ERC-20 token support (USDC, USDT, DAI)

## Supported Coins & Tokens

### Native Currencies

| Coin | Network | Confirmations |
|------|---------|---------------|
| BTC  | Bitcoin | 6 |
| LTC  | Litecoin | 12 |
| BCH  | Bitcoin Cash | 15 |
| ETH  | Ethereum | 12 |
| BNB  | BNB Smart Chain | 25 |
| SOL  | Solana | 1 |
| TRX  | Tron | 21 |

### ERC-20 Tokens (Ethereum)

| Token | Contract Address | Decimals |
|-------|-----------------|----------|
| USDC  | `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48` | 6 |
| USDT  | `0xdac17f958d2ee523a2206206994597c13d831ec7` | 6 |
| DAI   | `0x6b175474e89094c44da98b954eedeac495271d0f` | 18 |

## Setup & Installation

### Prerequisites

- Python 3.10+
- A Blockchair API key ([get one here](https://blockchair.com/api))

### Installation

```bash
chmod +x setup.sh
./setup.sh
```

### Environment Variables

Create a `.env` file in the project root:

```
BLOCKCHAIR_API_KEY="your_api_key_here"
COINGECKO_API_KEY="your_api_key_here"
```

### Running the Server

```bash
python3 main.py
```

The server will start on `http://localhost:5000`.

## API Documentation
...

## Tech Stack

- **Backend:** Python, Flask
- **Blockchain Data:** Blockchair API
- **Notifications:** Webhooks (HTTP POST)

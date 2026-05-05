# Sentinel

Sentinel monitors Alchemy Address Activity webhook events, enriches transfers with price and address context, checks anomaly rules, and pushes matching alerts to Telegram.

## Quick Start

```bash
uv sync
cp .env.example .env
uv run uvicorn src.main:app --reload --port 8000
```

Configure your Alchemy webhook URL as:

```text
https://your-public-url/webhook/alchemy
```

For local webhook testing, expose port `8000` with ngrok or another tunnel.

## Configuration

Environment variables:

- `TELEGRAM_BOT_TOKEN`: Telegram bot token from BotFather.
- `TELEGRAM_CHAT_ID`: Target chat or channel ID.
- `ALCHEMY_WEBHOOK_SECRET`: Alchemy webhook signing secret.
- `SENTINEL_REQUIRE_SIGNATURE`: Set to `true` in production.
- `SENTINEL_CHAIN`: Defaults to `base`.
- `SENTINEL_EXPLORER_TX_BASE`: Defaults to BaseScan transaction URLs.

Project config files:

- `config/rules.yaml`: Alert rules.
- `config/watchlist.yaml`: Addresses you plan to monitor in Alchemy.
- `config/address_labels.json`: Local address labels for clearer messages.

## Test A Webhook Locally

```bash
curl -X POST http://localhost:8000/webhook/alchemy \
  -H 'content-type: application/json' \
  -d '{
    "event": {
      "activity": [
        {
          "hash": "0xabc",
          "fromAddress": "0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
          "toAddress": "0x1111111111111111111111111111111111111111",
          "value": 2,
          "asset": "TEST",
          "rawContract": {"address": "0xtoken", "decimal": "18"},
          "metadata": {"blockTimestamp": "2026-05-05T00:00:00Z"}
        }
      ]
    }
  }'
```

If Telegram variables are missing, Sentinel prints alert messages to stdout instead of failing.

## Run Tests

```bash
uv run pytest
```

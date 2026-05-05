import json
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from src.config import get_settings
from src.enricher import Enricher
from src.models import AlertRecord, AlchemyWebhookPayload, TransferEvent
from src.rules import RuleEngine
from src.storage import AlertStorage
from src.telegram import TelegramNotifier
from src.webhook_verify import verify_alchemy_webhook_signature


settings = get_settings()
app = FastAPI(title="Sentinel", version="0.1.0")
rule_engine = RuleEngine(str(settings.rules_file))
enricher = Enricher(settings.labels_file)
storage = AlertStorage(settings.db_file)
notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/webhook/alchemy")
async def handle_alchemy_webhook(request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    if settings.require_signature:
        signature = request.headers.get("X-Alchemy-Signature")
        if not verify_alchemy_webhook_signature(
            raw_body, signature, settings.alchemy_webhook_secret
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload_data = json.loads(raw_body)
        payload = AlchemyWebhookPayload(**payload_data)
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc

    activities = payload.event.get("activity", [])
    processed = 0
    alerts_sent = 0

    for activity in activities:
        event = _activity_to_transfer_event(activity)
        if event is None:
            continue

        processed += 1
        enriched = await enricher.enrich_event(event)
        alerts = rule_engine.check_event(enriched, enriched.token_price)

        for alert in alerts:
            record = AlertRecord(
                tx_hash=enriched.tx_hash,
                from_address=enriched.from_address,
                to_address=enriched.to_address,
                value_usd=enriched.value_usd,
                severity=alert.severity,
                rule_id=alert.rule_id,
                reason=alert.reason,
                from_label=enriched.from_label,
                to_label=enriched.to_label,
            )
            storage.save_alert(record)
            sent = await notifier.send(_format_alert_message(record))
            alerts_sent += int(sent)

    return {"status": "ok", "processed": processed, "alerts_sent": alerts_sent}


def _activity_to_transfer_event(activity: dict[str, Any]) -> TransferEvent | None:
    tx_hash = activity.get("hash")
    from_address = activity.get("fromAddress")
    to_address = activity.get("toAddress")
    if not tx_hash or not from_address or not to_address:
        return None

    raw_contract = activity.get("rawContract") or {}
    value = _parse_float(activity.get("value"))
    timestamp = _parse_timestamp(activity.get("metadata", {}).get("blockTimestamp"))

    return TransferEvent(
        tx_hash=tx_hash,
        from_address=from_address,
        to_address=to_address,
        token_address=raw_contract.get("address"),
        asset=activity.get("asset"),
        value=value,
        decimals=_parse_int(raw_contract.get("decimal")),
        timestamp=timestamp,
        chain=settings.chain,
    )


def _format_alert_message(alert: AlertRecord) -> str:
    icon = "CRITICAL" if alert.severity == "critical" else alert.severity.upper()
    explorer_url = f"{settings.explorer_tx_base}{alert.tx_hash}"

    return (
        f"*{icon} on-chain alert*\n\n"
        f"From: `{alert.from_label.name}`\n"
        f"To: `{alert.to_label.name}`\n"
        f"Value: `${alert.value_usd:,.2f}`\n"
        f"Reason: {alert.reason}\n"
        f"[View transaction]({explorer_url})"
    )


def _parse_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except ValueError:
        return datetime.now(UTC)

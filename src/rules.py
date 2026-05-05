from datetime import UTC, datetime, timedelta
from typing import Any

from pydantic import BaseModel

from src.config import load_yaml
from src.models import RuleAlert, TransferEvent


class RuleConfig(BaseModel):
    id: str
    description: str
    enabled: bool = True
    trigger: dict[str, Any]
    severity: str = "medium"


class RuleEngine:
    def __init__(self, rules_file: str):
        config = load_yaml(rules_file)
        self.rules = [RuleConfig(**rule) for rule in config.get("rules", [])]
        self.event_history: list[TransferEvent] = []

    def check_event(self, event: TransferEvent, price_usd: float) -> list[RuleAlert]:
        alerts: list[RuleAlert] = []
        self._record_event(event)

        for rule in self.rules:
            if not rule.enabled:
                continue

            trigger_type = rule.trigger.get("type")
            if trigger_type == "transfer_amount":
                alert = self._check_transfer_amount(rule, event, price_usd)
            elif trigger_type == "tx_frequency":
                alert = self._check_tx_frequency(rule, event)
            else:
                alert = None

            if alert is not None:
                alerts.append(alert)

        return alerts

    def _record_event(self, event: TransferEvent) -> None:
        self.event_history.append(event)
        cutoff = datetime.now(UTC) - timedelta(hours=1)
        self.event_history = [
            item for item in self.event_history if _as_utc(item.timestamp) >= cutoff
        ]

    def _check_transfer_amount(
        self, rule: RuleConfig, event: TransferEvent, price_usd: float
    ) -> RuleAlert | None:
        min_value = float(rule.trigger.get("min_value_usd", float("inf")))
        value_usd = float(event.value or 0) * float(price_usd or 0)
        if value_usd <= min_value:
            return None

        return RuleAlert(
            rule_id=rule.id,
            severity=rule.severity,
            reason=f"Transfer value ${value_usd:,.2f} exceeds ${min_value:,.0f}",
        )

    def _check_tx_frequency(self, rule: RuleConfig, event: TransferEvent) -> RuleAlert | None:
        window_seconds = int(rule.trigger.get("window_seconds", 300))
        threshold = int(rule.trigger.get("threshold", 3))
        cutoff = datetime.now(UTC) - timedelta(seconds=window_seconds)
        from_address = event.from_address.lower()

        recent_txs = [
            item
            for item in self.event_history
            if item.from_address.lower() == from_address
            and _as_utc(item.timestamp) >= cutoff
        ]
        if len(recent_txs) < threshold:
            return None

        return RuleAlert(
            rule_id=rule.id,
            severity=rule.severity,
            reason=f"{len(recent_txs)} transactions in {window_seconds} seconds",
        )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)

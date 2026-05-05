from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AlchemyWebhookPayload(BaseModel):
    webhookId: str | None = None
    id: str | None = None
    createdAt: str | None = None
    type: str | None = None
    event: dict[str, Any] = Field(default_factory=dict)


class AddressLabel(BaseModel):
    name: str
    type: str = "unknown"
    risk: str = "unknown"


class TransferEvent(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    token_address: str | None = None
    asset: str | None = None
    value: float = 0.0
    decimals: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    chain: str = "base"


class EnrichedEvent(TransferEvent):
    token_price: float = 0.0
    value_usd: float = 0.0
    from_label: AddressLabel
    to_label: AddressLabel


class RuleAlert(BaseModel):
    rule_id: str
    severity: Literal["critical", "high", "medium", "low"]
    reason: str


class AlertRecord(BaseModel):
    tx_hash: str
    from_address: str
    to_address: str
    value_usd: float
    severity: str
    rule_id: str
    reason: str
    from_label: AddressLabel
    to_label: AddressLabel
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

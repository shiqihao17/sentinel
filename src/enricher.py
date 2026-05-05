import json
from pathlib import Path
from typing import Any

import httpx

from src.models import AddressLabel, EnrichedEvent, TransferEvent


class Enricher:
    def __init__(self, labels_file: str | Path):
        with Path(labels_file).open("r", encoding="utf-8") as file:
            raw_labels = json.load(file)
        self.labels = {key.lower(): value for key, value in raw_labels.items()}

    async def get_token_price(self, token_address: str | None) -> float:
        if not token_address:
            return 0.0

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
                )
                response.raise_for_status()
                data: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError):
            return 0.0

        pairs = data.get("pairs") or []
        if not pairs:
            return 0.0

        try:
            return float(pairs[0].get("priceUsd") or 0)
        except (TypeError, ValueError):
            return 0.0

    def get_address_label(self, address: str | None) -> AddressLabel:
        normalized = (address or "").lower()
        label = self.labels.get(normalized)
        if label:
            return AddressLabel(**label)

        short = f"{normalized[:6]}...{normalized[-4:]}" if normalized else "unknown"
        return AddressLabel(name=short)

    async def enrich_event(self, event: TransferEvent) -> EnrichedEvent:
        token_price = await self.get_token_price(event.token_address)
        value_usd = token_price * float(event.value or 0)

        return EnrichedEvent(
            **event.model_dump(),
            token_price=token_price,
            value_usd=value_usd,
            from_label=self.get_address_label(event.from_address),
            to_label=self.get_address_label(event.to_address),
        )

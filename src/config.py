from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    alchemy_webhook_secret: str | None = None
    require_signature: bool = False
    chain: str = "base"
    explorer_tx_base: str = "https://basescan.org/tx/"
    rules_file: Path = PROJECT_ROOT / "config" / "rules.yaml"
    labels_file: Path = PROJECT_ROOT / "config" / "address_labels.json"
    watchlist_file: Path = PROJECT_ROOT / "config" / "watchlist.yaml"
    db_file: Path = PROJECT_ROOT / "alerts.db"


@lru_cache
def get_settings() -> Settings:
    import os

    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        alchemy_webhook_secret=os.getenv("ALCHEMY_WEBHOOK_SECRET"),
        require_signature=os.getenv("SENTINEL_REQUIRE_SIGNATURE", "false").lower()
        in {"1", "true", "yes"},
        chain=os.getenv("SENTINEL_CHAIN", "base"),
        explorer_tx_base=os.getenv(
            "SENTINEL_EXPLORER_TX_BASE", "https://basescan.org/tx/"
        ),
    )


def load_yaml(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}

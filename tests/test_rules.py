from datetime import UTC, datetime, timedelta

from src.models import TransferEvent
from src.rules import RuleEngine


def test_large_transfer_rule_triggers():
    engine = RuleEngine("config/rules.yaml")
    event = TransferEvent(
        tx_hash="0xabc",
        from_address="0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
        to_address="0x1111111111111111111111111111111111111111",
        token_address="0xtoken",
        value=2,
    )

    alerts = engine.check_event(event, price_usd=30000)

    assert [alert.rule_id for alert in alerts] == ["large_transfer"]
    assert alerts[0].severity == "critical"


def test_large_transfer_rule_ignores_small_values():
    engine = RuleEngine("config/rules.yaml")
    event = TransferEvent(
        tx_hash="0xabc",
        from_address="0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
        to_address="0x1111111111111111111111111111111111111111",
        token_address="0xtoken",
        value=1,
    )

    assert engine.check_event(event, price_usd=10) == []


def test_frequency_rule_triggers_per_sender():
    engine = RuleEngine("config/rules.yaml")
    now = datetime.now(UTC)

    for index in range(3):
        event = TransferEvent(
            tx_hash=f"0x{index}",
            from_address="0xb1058c959987e3513600eb5b4fd82aeee2a0e4f9",
            to_address="0x1111111111111111111111111111111111111111",
            token_address="0xtoken",
            value=1,
            timestamp=now + timedelta(seconds=index),
        )
        alerts = engine.check_event(event, price_usd=1)

    assert any(alert.rule_id == "ai_agent_burst" for alert in alerts)

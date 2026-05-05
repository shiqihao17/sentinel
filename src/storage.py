import sqlite3
from pathlib import Path
from typing import Any

from src.models import AlertRecord


class AlertStorage:
    def __init__(self, db_file: str | Path):
        self.db_file = Path(db_file)
        self.init_db()

    def init_db(self) -> None:
        with sqlite3.connect(self.db_file) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY,
                    tx_hash TEXT,
                    from_address TEXT,
                    to_address TEXT,
                    value_usd REAL,
                    severity TEXT,
                    rule_id TEXT,
                    reason TEXT,
                    created_at TEXT,
                    pushed_at TEXT NULL,
                    UNIQUE(tx_hash, rule_id)
                )
                """
            )

    def save_alert(self, alert: AlertRecord) -> bool:
        try:
            with sqlite3.connect(self.db_file) as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO alerts
                    (tx_hash, from_address, to_address, value_usd, severity, rule_id, reason, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.tx_hash,
                        alert.from_address,
                        alert.to_address,
                        alert.value_usd,
                        alert.severity,
                        alert.rule_id,
                        alert.reason,
                        alert.created_at.isoformat(),
                    ),
                )
            return True
        except sqlite3.Error as exc:
            print(f"Save alert failed: {exc}")
            return False

    def get_recent_alerts(self, seconds: int = 30, from_address: str | None = None) -> list[dict[str, Any]]:
        query = """
            SELECT id, tx_hash, from_address, to_address, value_usd, severity, rule_id, reason, created_at, pushed_at
            FROM alerts
            WHERE datetime(created_at) > datetime('now', '-' || ? || ' seconds')
        """
        params: list[Any] = [seconds]

        if from_address:
            query += " AND lower(from_address) = lower(?)"
            params.append(from_address)

        with sqlite3.connect(self.db_file) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

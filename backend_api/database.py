"""SQLite persistence for alerts. OWNER: Dev 2. Zero-config: one file, auto-created."""
from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

DB_PATH = os.path.join(os.path.dirname(__file__), "safenet.db")


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db() -> None:
    with _conn() as c:
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                alert_id   TEXT PRIMARY KEY,
                child_id   TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload    TEXT NOT NULL   -- full Alert JSON (contract C)
            )
            """
        )


def save_alert(alert: dict[str, Any]) -> None:
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO alerts (alert_id, child_id, created_at, payload) "
            "VALUES (?, ?, ?, ?)",
            (alert["alert_id"], alert["child_id"], alert["created_at"], json.dumps(alert)),
        )


def get_alerts(child_id: str | None = None) -> list[dict[str, Any]]:
    with _conn() as c:
        if child_id:
            rows = c.execute(
                "SELECT payload FROM alerts WHERE child_id=? ORDER BY created_at DESC",
                (child_id,),
            ).fetchall()
        else:
            rows = c.execute(
                "SELECT payload FROM alerts ORDER BY created_at DESC"
            ).fetchall()
    return [json.loads(r["payload"]) for r in rows]

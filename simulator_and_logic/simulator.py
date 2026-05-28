"""
Fake WhatsApp — streams a scripted conversation to the backend. OWNER: Dev 4.

Acts as an external HTTP client. Sends each message as contract A to POST /ingest,
with a sliding window of context_before/context_after, at a variable pace.

Run (backend must be up on :8000):
    python simulator.py
    python simulator.py --conversation conversations/escalation_demo.json --speed 0.5
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime

import requests

BACKEND_URL = "http://localhost:8000/ingest"
CONTEXT_WINDOW = 2  # messages of context on each side


def run(conversation_path: str, speed: float) -> None:
    with open(conversation_path, encoding="utf-8") as f:
        convo = json.load(f)

    msgs = convo["messages"]
    for i, m in enumerate(msgs):
        payload = {
            "message_id": f"msg_{uuid.uuid4().hex[:8]}",
            "group_name": convo["group_name"],
            "sender_id": m["sender_id"],
            "sender_name": m["sender_name"],
            "child_id": convo["child_id"],
            "text": m["text"],
            "media_url": m.get("media_url"),
            "timestamp": datetime.now().isoformat(),
            "context_before": [x["text"] for x in msgs[max(0, i - CONTEXT_WINDOW):i]],
            "context_after": [x["text"] for x in msgs[i + 1:i + 1 + CONTEXT_WINDOW]],
        }
        _send(payload)
        time.sleep(m.get("delay_sec", 2) * speed)


def _send(payload: dict) -> None:
    label = f'{payload["sender_name"]}: {payload["text"]}'
    try:
        r = requests.post(BACKEND_URL, json=payload, timeout=10)
        res = r.json()
        flag = "🚨 ALERT" if res.get("alert_created") else "ok"
        print(f"[{flag}] {label}")
    except Exception as exc:  # noqa: BLE001
        print(f"[send failed] {label} ({exc})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--conversation", default="conversations/escalation_demo.json")
    p.add_argument("--speed", type=float, default=1.0, help="<1 faster, >1 slower")
    args = p.parse_args()
    run(args.conversation, args.speed)

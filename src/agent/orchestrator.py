from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _tools_url() -> str:
    load_dotenv(".env")
    return os.getenv("TOOLS_SERVER_URL", "http://localhost:8000").rstrip("/")


def _post(client: httpx.Client, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    res = client.post(path, json=payload, timeout=30.0)
    res.raise_for_status()
    return res.json()


def main() -> None:
    base = _tools_url()

    with httpx.Client(base_url=base) as client:
        detected = _post(
            client,
            "/tools/detect_abandoned_carts",
            {"lookback_minutes": 1440, "abandonment_minutes": 30, "max_candidates": 20},
        )

        candidates: List[Dict[str, Any]] = detected.get("candidates", [])
        top = candidates[:3]

        print(f"Detected {len(candidates)} abandoned cart candidates; processing top {len(top)}...\n")

        for c in top:
            cart_id = c["cart_id"]
            print(f"--- Cart {cart_id} (value={c.get('cart_value')}) ---")

            analysis = _post(client, "/tools/analyze_abandonment", {"cart_id": cart_id})
            diagnosis = analysis.get("diagnosis", {})

            customer = _post(
                client,
                "/tools/get_customer_profile",
                {"customer_id": c["customer_id"]},
            ).get("profile", {})

            similar = _post(
                client,
                "/tools/find_similar_abandonments",
                {
                    "similarity": {
                        "root_cause": diagnosis.get("root_cause", "unknown"),
                        "segment": customer.get("segment", "standard"),
                        "cart_value": c.get("cart_value", 0.0),
                    },
                    "lookback_days": 180,
                    "size": 20,
                },
            )

            decision = _post(
                client,
                "/tools/decide_recovery_action",
                {
                    "cart": c,
                    "diagnosis": diagnosis,
                    "customer": customer,
                    "similar_stats": similar.get("stats", []),
                },
            )

            action = decision.get("action", {})
            rationale = decision.get("rationale")
            print(f"Diagnosis: {diagnosis.get('root_cause')} | Action: {action.get('type')} | Rationale: {rationale}")

            sent = _post(
                client,
                "/tools/trigger_recovery_action",
                {"cart": c, "customer": customer, "action": action},
            )
            print(f"Trigger result: {sent}\n")

            if sent.get("status") == "sent":
                rec = _post(
                    client,
                    "/tools/record_recovery_attempt",
                    {
                        "cart": c,
                        "customer": customer,
                        "diagnosis": diagnosis,
                        "action": action,
                        "sent_at": _utcnow().isoformat(),
                    },
                )
                print(f"Recorded recovery attempt: {rec}\n")


if __name__ == "__main__":
    main()

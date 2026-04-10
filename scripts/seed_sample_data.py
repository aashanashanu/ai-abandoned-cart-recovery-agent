import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
import boto3
import json
import random

def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

def main() -> None:
    # Send to EventBridge; Lambda will handle indexing into Elasticsearch
    eb = boto3.client("events", region_name="us-east-1")
    event_bus = os.getenv("EVENT_BUS_NAME")
    if not event_bus:
        raise ValueError("EVENT_BUS_NAME environment variable is required")
    print(f"Using EventBus: {event_bus}")

    now = datetime.now(timezone.utc)

    # Enhanced customer profiles for diverse scenarios
    customers = [
        {
            "_index": "customer_profiles",
            "_id": "cust_001",
            "_source": {
                "@timestamp": utc(now),
                "customer_id": "cust_001",
                "email": "alex@example.com",
                "phone": "+155555501",
                "push_token": "push_token_001",
                "segment": "vip",
                "lifetime_value": 5000.0,
                "preferred_channel": "email",
                "fraud_risk": "low",
                "locale": "en-US",
                "timezone": "America/Chicago",
                "last_purchase_at": utc(now - timedelta(days=12)),
            },
        },
        {
            "_index": "customer_profiles",
            "_id": "cust_002",
            "_source": {
                "@timestamp": utc(now),
                "customer_id": "cust_002",
                "email": "jamie@example.com",
                "phone": "+155555502",
                "push_token": "push_token_002",
                "segment": "standard",
                "lifetime_value": 1800.0,
                "preferred_channel": "push",
                "fraud_risk": "low",
                "locale": "en-US",
                "timezone": "America/Chicago",
                "last_purchase_at": utc(now - timedelta(days=45)),
            },
        },
        {
            "_index": "customer_profiles",
            "_id": "cust_003",
            "_source": {
                "@timestamp": utc(now),
                "customer_id": "cust_003",
                "email": "sam@example.com",
                "phone": "+155555503",
                "push_token": "push_token_003",
                "segment": "high_fraud_risk",
                "lifetime_value": 250.0,
                "preferred_channel": "email",
                "fraud_risk": "high",
                "locale": "en-US",
                "timezone": "America/Chicago",
                "last_purchase_at": utc(now - timedelta(days=30)),
            },
        },
        {
            "_index": "customer_profiles",
            "_id": "cust_004",
            "_source": {
                "@timestamp": utc(now),
                "customer_id": "cust_004",
                "email": "taylor@example.com",
                "phone": "+155555504",
                "push_token": "push_token_004",
                "segment": "standard",
                "lifetime_value": 0.0,
                "preferred_channel": "email",
                "fraud_risk": "low",
                "locale": "en-US",
                "timezone": "America/Chicago",
                "last_purchase_at": None,
            },
        },
        {
            "_index": "customer_profiles",
            "_id": "cust_005",
            "_source": {
                "@timestamp": utc(now),
                "customer_id": "cust_005",
                "email": "maria@example.com",
                "phone": "+4479123456",
                "push_token": "push_token_005",
                "segment": "standard",
                "lifetime_value": 850.0,
                "preferred_channel": "email",
                "fraud_risk": "medium",
                "locale": "en-GB",
                "timezone": "Europe/London",
                "last_purchase_at": utc(now - timedelta(days=15)),
            },
        },
    ]

    # Enhanced cart events for all scenarios
    cart_events = [
        # Scenario 1: VIP customer with payment failure
        {
            "_index": "cart_events",
            "_id": "cart_evt_001",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=85)),
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "session_id": "sess_aaa",
                "event_type": "add_to_cart",
                "product_id": "sku_hoodie_01",
                "quantity": 1,
                "unit_price": 89.0,
                "cart_value": 89.0,
                "currency": "USD",
                "device_type": "mobile",
                "page": "/product/sku_hoodie_01",
                "referrer": "google",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_002",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=80)),
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "session_id": "sess_aaa",
                "event_type": "add_to_cart",
                "product_id": "sku_shoes_02",
                "quantity": 1,
                "unit_price": 95.0,
                "cart_value": 184.0,
                "currency": "USD",
                "device_type": "mobile",
                "page": "/product/sku_shoes_02",
                "referrer": "direct",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_003",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=75)),
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "session_id": "sess_aaa",
                "event_type": "add_to_cart",
                "product_id": "sku_hat_03",
                "quantity": 1,
                "unit_price": 45.0,
                "cart_value": 229.0,
                "currency": "USD",
                "device_type": "mobile",
                "page": "/product/sku_hat_03",
                "referrer": "direct",
            },
        },
        # Scenario 2: Standard customer with shipping cost issue
        {
            "_index": "cart_events",
            "_id": "cart_evt_004",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=50)),
                "cart_id": "cart_2002",
                "customer_id": "cust_002",
                "session_id": "sess_bbb",
                "event_type": "add_to_cart",
                "product_id": "sku_socks_02",
                "quantity": 2,
                "unit_price": 12.0,
                "cart_value": 24.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_socks_02",
                "referrer": "email_campaign",
            },
        },
        # Scenario 3: Standard customer with high item count for discount
        {
            "_index": "cart_events",
            "_id": "cart_evt_005",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=95)),
                "cart_id": "cart_3003",
                "customer_id": "cust_004",
                "session_id": "sess_ccc",
                "event_type": "add_to_cart",
                "product_id": "sku_jacket_03",
                "quantity": 1,
                "unit_price": 155.0,
                "cart_value": 155.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_jacket_03",
                "referrer": "direct",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_006",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=90)),
                "cart_id": "cart_3003",
                "customer_id": "cust_004",
                "session_id": "sess_ccc",
                "event_type": "add_to_cart",
                "product_id": "sku_shirt_04",
                "quantity": 1,
                "unit_price": 85.0,
                "cart_value": 240.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_shirt_04",
                "referrer": "direct",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_007",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=85)),
                "cart_id": "cart_3003",
                "customer_id": "cust_004",
                "session_id": "sess_ccc",
                "event_type": "add_to_cart",
                "product_id": "sku_pants_05",
                "quantity": 1,
                "unit_price": 75.0,
                "cart_value": 315.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_pants_05",
                "referrer": "direct",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_008",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=80)),
                "cart_id": "cart_3003",
                "customer_id": "cust_004",
                "session_id": "sess_ccc",
                "event_type": "add_to_cart",
                "product_id": "sku_shoes_06",
                "quantity": 1,
                "unit_price": 95.0,
                "cart_value": 410.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_shoes_06",
                "referrer": "direct",
            },
        },
        # Scenario 4: High fraud risk customer
        {
            "_index": "cart_events",
            "_id": "cart_evt_009",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=70)),
                "cart_id": "cart_4004",
                "customer_id": "cust_003",
                "session_id": "sess_ddd",
                "event_type": "add_to_cart",
                "product_id": "sku_hat_04",
                "quantity": 2,
                "unit_price": 22.0,
                "cart_value": 44.0,
                "currency": "USD",
                "device_type": "mobile",
                "page": "/product/sku_hat_04",
                "referrer": "google",
            },
        },
        # Scenario 5: International customer for learning
        {
            "_index": "cart_events",
            "_id": "cart_evt_010",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=200)),
                "cart_id": "cart_5005",
                "customer_id": "cust_005",
                "session_id": "sess_eee",
                "event_type": "add_to_cart",
                "product_id": "sku_bottle_05",
                "quantity": 1,
                "unit_price": 18.0,
                "cart_value": 18.0,
                "currency": "USD",
                "device_type": "desktop",
                "page": "/product/sku_bottle_05",
                "referrer": "email_campaign",
            },
        },
    ]

    # Enhanced checkout events
    checkout_events = [
        # Scenario 1: Payment failure for VIP
        {
            "_index": "checkout_events",
            "_id": "chk_evt_001",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=78)),
                "checkout_id": "chk_9001",
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "session_id": "sess_aaa",
                "step": "payment_failed",
                "status": "started",
                "shipping_method": "standard",
                "shipping_cost": 7.0,
                "tax": 18.4,
                "total": 254.4,
                "currency": "USD",
                "payment_method": "visa",
            },
        },
        # Scenario 2: Shipping step abandonment
        {
            "_index": "checkout_events",
            "_id": "chk_evt_002",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=46)),
                "checkout_id": "chk_9002",
                "cart_id": "cart_2002",
                "customer_id": "cust_002",
                "session_id": "sess_bbb",
                "step": "shipping_failed",
                "status": "started",
                "shipping_method": "standard",
                "shipping_cost": 6.0,
                "tax": 2.4,
                "total": 32.4,
                "currency": "USD",
                "payment_method": "unknown",
            },
        },
        # Scenario 4: Payment failure for high fraud risk
        {
            "_index": "checkout_events",
            "_id": "chk_evt_003",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=68)),
                "checkout_id": "chk_9003",
                "cart_id": "cart_4004",
                "customer_id": "cust_003",
                "session_id": "sess_ddd",
                "step": "payment_failed",
                "status": "started",
                "shipping_method": "standard",
                "shipping_cost": 5.0,
                "tax": 4.4,
                "total": 53.4,
                "currency": "USD",
                "payment_method": "visa",
            },
        },
        # Scenario 5: Checkout friction
        {
            "_index": "checkout_events",
            "_id": "chk_evt_004",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=195)),
                "checkout_id": "chk_9004",
                "cart_id": "cart_5005",
                "customer_id": "cust_005",
                "session_id": "sess_eee",
                "step": "shipping_failed",
                "status": "started",
                "shipping_method": "express",
                "shipping_cost": 12.0,
                "tax": 1.8,
                "total": 31.8,
                "currency": "USD",
                "payment_method": "unknown",
            },
        },
    ]

    # Enhanced payment logs
    payment_logs = [
        # Scenario 1: Card declined for VIP
        {
            "_index": "payment_logs",
            "_id": "pay_log_001",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=77)),
                "payment_id": "pay_7001",
                "checkout_id": "chk_9001",
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "provider": "stripe",
                "status": "failed",
                "failure_code": "card_declined",
                "failure_message": "Card was declined",
                "retryable": True,
                "gateway_latency_ms": 850,
                "attempt": 1,
            },
        },
        # Scenario 4: Card declined for high fraud risk
        {
            "_index": "payment_logs",
            "_id": "pay_log_002",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=67)),
                "payment_id": "pay_7002",
                "checkout_id": "chk_9003",
                "cart_id": "cart_4004",
                "customer_id": "cust_003",
                "provider": "stripe",
                "status": "failed",
                "failure_code": "card_declined",
                "failure_message": "Card was declined",
                "retryable": True,
                "gateway_latency_ms": 1200,
                "attempt": 1,
            },
        },
    ]

    # Enhanced session metrics
    session_metrics = [
        # Scenario 1: Good performance
        {
            "_index": "session_metrics",
            "_id": "sess_met_001",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=78)),
                "session_id": "sess_aaa",
                "customer_id": "cust_001",
                "route": "/checkout/payment",
                "device_type": "mobile",
                "p95_latency_ms": 1200,
                "error_rate": 0.02,
                "apdex": 0.78,
            },
        },
        # Scenario 2: Good performance
        {
            "_index": "session_metrics",
            "_id": "sess_met_002",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=45)),
                "session_id": "sess_bbb",
                "customer_id": "cust_002",
                "route": "/checkout/shipping",
                "device_type": "desktop",
                "p95_latency_ms": 380,
                "error_rate": 0.0,
                "apdex": 0.94,
            },
        },
        # Scenario 3: Poor performance (no checkout)
        {
            "_index": "session_metrics",
            "_id": "sess_met_003",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=94)),
                "session_id": "sess_ccc",
                "customer_id": "cust_004",
                "route": "/product/sku_jacket_03",
                "device_type": "desktop",
                "p95_latency_ms": 1750,
                "error_rate": 0.07,
                "apdex": 0.72,
            },
        },
        # Scenario 4: Good performance
        {
            "_index": "session_metrics",
            "_id": "sess_met_004",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=68)),
                "session_id": "sess_ddd",
                "customer_id": "cust_003",
                "route": "/checkout/shipping",
                "device_type": "mobile",
                "p95_latency_ms": 420,
                "error_rate": 0.0,
                "apdex": 0.93,
            },
        },
        # Scenario 5: Moderate performance
        {
            "_index": "session_metrics",
            "_id": "sess_met_005",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=195)),
                "session_id": "sess_eee",
                "customer_id": "cust_005",
                "route": "/checkout/shipping",
                "device_type": "desktop",
                "p95_latency_ms": 650,
                "error_rate": 0.03,
                "apdex": 0.85,
            },
        },
    ]

    # Enhanced recovery history for learning
    recovery_history = [
        # Success with payment retry for VIP
        {
            "_index": "recovery_history",
            "_id": "rec_hist_001",
            "_source": {
                "@timestamp": utc(now - timedelta(days=14)),
                "recovery_id": "rec_001",
                "cart_id": "cart_hist_001",
                "customer_id": "cust_001",
                "segment": "vip",
                "cart_value": 110.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "payment_failure", "signals": ["card_declined"]},
                "action": {
                    "type": "payment_retry",
                    "channel": "email",
                    "discount_percent": 0.0,
                    "free_shipping": False,
                    "template": "retry_payment"
                },
                "sent_at": utc(now - timedelta(days=14, minutes=10)),
                "outcome": {
                    "status": "recovered",
                    "order_id": "ord_abc",
                    "revenue_recovered": 110.0,
                    "outcome_at": utc(now - timedelta(days=14, minutes=2))
                }
            },
        },
        # Success with free shipping for standard
        {
            "_index": "recovery_history",
            "_id": "rec_hist_002",
            "_source": {
                "@timestamp": utc(now - timedelta(days=60)),
                "recovery_id": "rec_002",
                "cart_id": "cart_hist_002",
                "customer_id": "cust_002",
                "segment": "standard",
                "cart_value": 35.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "pricing_shipping", "signals": ["high_shipping_cost"]},
                "action": {
                    "type": "free_shipping",
                    "channel": "push",
                    "discount_percent": 0.0,
                    "free_shipping": True,
                    "template": "free_shipping_offer"
                },
                "sent_at": utc(now - timedelta(days=60, minutes=5)),
                "outcome": {
                    "status": "recovered",
                    "order_id": "ord_def",
                    "revenue_recovered": 35.0,
                    "outcome_at": utc(now - timedelta(days=60, minutes=1))
                }
            },
        },
        # Success with reminder for performance issues
        {
            "_index": "recovery_history",
            "_id": "rec_hist_003",
            "_source": {
                "@timestamp": utc(now - timedelta(days=21)),
                "recovery_id": "rec_003",
                "cart_id": "cart_hist_003",
                "customer_id": "cust_004",
                "segment": "standard",
                "cart_value": 165.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "performance_latency", "signals": ["high_latency", "high_error_rate"]},
                "action": {
                    "type": "reminder",
                    "channel": "email",
                    "discount_percent": 0.0,
                    "free_shipping": False,
                    "template": "supportive_reminder",
                },
                "sent_at": utc(now - timedelta(days=21, minutes=4)),
                "outcome": {
                    "status": "recovered",
                    "order_id": "ord_lat",
                    "revenue_recovered": 165.0,
                    "outcome_at": utc(now - timedelta(days=21, minutes=1)),
                },
            },
        },
        # Success with reminder for checkout friction
        {
            "_index": "recovery_history",
            "_id": "rec_hist_004",
            "_source": {
                "@timestamp": utc(now - timedelta(days=35)),
                "recovery_id": "rec_004",
                "cart_id": "cart_hist_004",
                "customer_id": "cust_005",
                "segment": "standard",
                "cart_value": 55.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "checkout_friction", "signals": ["stalled_before_payment"]},
                "action": {
                    "type": "reminder",
                    "channel": "email",
                    "discount_percent": 0.0,
                    "free_shipping": False,
                    "template": "simple_reminder",
                },
                "sent_at": utc(now - timedelta(days=35, minutes=7)),
                "outcome": {
                    "status": "recovered",
                    "order_id": "ord_fric",
                    "revenue_recovered": 55.0,
                    "outcome_at": utc(now - timedelta(days=35, minutes=2)),
                },
            },
        },
        # Failed recovery with discount (for learning)
        {
            "_index": "recovery_history",
            "_id": "rec_hist_005",
            "_source": {
                "@timestamp": utc(now - timedelta(days=40)),
                "recovery_id": "rec_005",
                "cart_id": "cart_hist_005",
                "customer_id": "cust_002",
                "segment": "standard",
                "cart_value": 58.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "checkout_friction", "signals": ["stalled_before_payment"]},
                "action": {
                    "type": "discount",
                    "channel": "email",
                    "discount_percent": 7.5,
                    "free_shipping": False,
                    "template": "discount_offer",
                },
                "sent_at": utc(now - timedelta(days=40, minutes=6)),
                "outcome": {
                    "status": "not_recovered",
                    "order_id": None,
                    "revenue_recovered": 0.0,
                    "outcome_at": utc(now - timedelta(days=40, minutes=1)),
                },
            },
        },
        # Failed recovery for high fraud risk (guardrail)
        {
            "_index": "recovery_history",
            "_id": "rec_hist_006",
            "_source": {
                "@timestamp": utc(now - timedelta(days=10)),
                "recovery_id": "rec_006",
                "cart_id": "cart_hist_006",
                "customer_id": "cust_003",
                "segment": "standard",
                "cart_value": 19.0,
                "currency": "USD",
                "diagnosis": {"root_cause": "unknown", "signals": ["insufficient_signals"]},
                "action": {
                    "type": "reminder",
                    "channel": "push",
                    "discount_percent": 0.0,
                    "free_shipping": False,
                    "template": "simple_reminder",
                },
                "sent_at": utc(now - timedelta(days=10, minutes=3)),
                "outcome": {
                    "status": "not_recovered",
                    "order_id": None,
                    "revenue_recovered": 0.0,
                    "outcome_at": utc(now - timedelta(days=10, minutes=1)),
                },
            },
        },
    ]

    # Send documents as EventBridge events; Lambda will index into Elasticsearch
    all_docs = []
    all_docs.extend(customers)
    all_docs.extend(cart_events)
    all_docs.extend(checkout_events)
    all_docs.extend(payment_logs)
    all_docs.extend(session_metrics)
    all_docs.extend(recovery_history)

    def _make_entry(doc):
        return {
            "Source": "ai-abandoned-cart",
            "DetailType": doc["_index"],
            "Detail": json.dumps({
                "_index": doc["_index"],
                "_id": doc.get("_id"),
                "_source": doc.get("_source"),
            }),
            "EventBusName": event_bus,
        }

    # EventBridge PutEvents accepts up to 10 entries at a time
    batch = []
    sent = 0
    accepted = 0
    for doc in all_docs:
        batch.append(_make_entry(doc))
        if len(batch) == 10:
            resp = eb.put_events(Entries=batch)
            batch_accepted = sum(1 for e in resp.get("Entries", []) if "ErrorCode" not in e)
            batch_failed = len(batch) - batch_accepted
            if batch_failed > 0:
                print(f"Batch failed: {batch_failed}/{len(batch)} events rejected")
                for e in resp.get("Entries", []):
                    if "ErrorCode" in e:
                        print(f"  Error: {e.get('ErrorCode')} - {e.get('ErrorMessage')}")
            accepted += batch_accepted
            sent += len(batch)
            batch = []

    if batch:
        resp = eb.put_events(Entries=batch)
        batch_accepted = sum(1 for e in resp.get("Entries", []) if "ErrorCode" not in e)
        batch_failed = len(batch) - batch_accepted
        if batch_failed > 0:
            print(f"Final batch failed: {batch_failed}/{len(batch)} events rejected")
            for e in resp.get("Entries", []):
                if "ErrorCode" in e:
                    print(f"  Error: {e.get('ErrorCode')} - {e.get('ErrorMessage')}")
        accepted += batch_accepted
        sent += len(batch)

    print(f"Enhanced sample data events sent to EventBridge: attempted={sent} accepted={accepted}")
    print(f"Generated {len(customers)} customer profiles (events)")
    print(f"Generated {len(cart_events)} cart events (events)")
    print(f"Generated {len(checkout_events)} checkout events (events)")
    print(f"Generated {len(payment_logs)} payment logs (events)")
    print(f"Generated {len(session_metrics)} session metrics (events)")
    print(f"Generated {len(recovery_history)} recovery history entries (events)")

    print("\n=== Test Scenarios Created ===")
    print("1. cart_1001: VIP customer with payment failure -> payment_retry")
    print("2. cart_2002: Standard customer with shipping cost -> free_shipping")
    print("3. cart_3003: New customer with performance issues -> reminder")
    print("4. cart_4004: High fraud risk customer -> reminder (guardrail)")
    print("5. cart_5005: International customer -> based on history")

if __name__ == "__main__":
    main()
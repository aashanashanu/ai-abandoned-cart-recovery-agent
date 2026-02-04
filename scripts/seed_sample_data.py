import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


def utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_es_client() -> Elasticsearch:
    load_dotenv(".env")

    es_url = os.getenv("ES_URL", "http://localhost:9200")
    api_key = os.getenv("ES_API_KEY") or None
    username = os.getenv("ES_USERNAME") or None
    password = os.getenv("ES_PASSWORD") or None

    if api_key:
        return Elasticsearch(es_url, api_key=api_key)

    if username and password:
        return Elasticsearch(es_url, basic_auth=(username, password))

    return Elasticsearch(es_url)


def main() -> None:
    es = build_es_client()

    now = datetime.now(timezone.utc)

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
                "lifetime_value": 4200.0,
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
                "lifetime_value": 180.0,
                "preferred_channel": "push",
                "fraud_risk": "low",
                "locale": "en-US",
                "timezone": "America/Chicago",
                "last_purchase_at": utc(now - timedelta(days=45)),
            },
        },
    ]

    cart_events = [
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
                "event_type": "view_cart",
                "product_id": "sku_hoodie_01",
                "quantity": 1,
                "unit_price": 89.0,
                "cart_value": 89.0,
                "currency": "USD",
                "device_type": "mobile",
                "page": "/cart",
                "referrer": "direct",
            },
        },
        {
            "_index": "cart_events",
            "_id": "cart_evt_003",
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
    ]

    checkout_events = [
        {
            "_index": "checkout_events",
            "_id": "chk_evt_001",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=78)),
                "checkout_id": "chk_9001",
                "cart_id": "cart_1001",
                "customer_id": "cust_001",
                "session_id": "sess_aaa",
                "step": "payment",
                "status": "started",
                "shipping_method": "standard",
                "shipping_cost": 7.0,
                "tax": 8.3,
                "total": 104.3,
                "currency": "USD",
                "payment_method": "visa",
            },
        },
        {
            "_index": "checkout_events",
            "_id": "chk_evt_002",
            "_source": {
                "@timestamp": utc(now - timedelta(minutes=46)),
                "checkout_id": "chk_9002",
                "cart_id": "cart_2002",
                "customer_id": "cust_002",
                "session_id": "sess_bbb",
                "step": "shipping",
                "status": "started",
                "shipping_method": "standard",
                "shipping_cost": 6.0,
                "tax": 2.1,
                "total": 32.1,
                "currency": "USD",
                "payment_method": "unknown",
            },
        },
    ]

    payment_logs = [
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
                "retryable": true,
                "gateway_latency_ms": 850,
                "attempt": 1,
            },
        }
    ]

    session_metrics = [
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
        }
    ]

    recovery_history = [
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
                    "free_shipping": false,
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
                    "free_shipping": true,
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
        }
    ]

    actions = []
    actions.extend(customers)
    actions.extend(cart_events)
    actions.extend(checkout_events)
    actions.extend(payment_logs)
    actions.extend(session_metrics)
    actions.extend(recovery_history)

    bulk(es, actions)
    es.indices.refresh(index=[
        "customer_profiles",
        "cart_events",
        "checkout_events",
        "payment_logs",
        "session_metrics",
        "recovery_history",
    ])

    print("Seeded sample data.")


if __name__ == "__main__":
    main()

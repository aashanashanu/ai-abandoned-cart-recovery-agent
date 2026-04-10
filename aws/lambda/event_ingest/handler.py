import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from elasticsearch import Elasticsearch


# Initialize Elasticsearch client (singleton, reused across warm starts)
_es_client = None


def _get_es_client():
    """Get or create Elasticsearch client with proper authentication"""
    global _es_client
    if _es_client is not None:
        return _es_client
    
    es_endpoint = os.getenv("ES_ENDPOINT")
    api_key = os.getenv("ES_API_KEY")
    username = os.getenv("ES_USERNAME")
    password = os.getenv("ES_PASSWORD")
    
    if not es_endpoint:
        print("ES_ENDPOINT not set; cannot create ES client")
        return None
    
    # API key authentication (recommended)
    if api_key:
        print(f"Connecting to Elasticsearch with API key")
        _es_client = Elasticsearch(
            es_endpoint,
            api_key=api_key,
            request_timeout=10,
            verify_certs=False  # For AWS Elastic Cloud self-signed certs
        )
    # Basic authentication fallback
    elif username and password:
        print(f"Connecting to Elasticsearch with basic auth")
        _es_client = Elasticsearch(
            es_endpoint,
            basic_auth=(username, password),
            request_timeout=10,
            verify_certs=False
        )
    else:
        print("No authentication configured")
        _es_client = Elasticsearch(
            es_endpoint,
            request_timeout=10,
            verify_certs=False
        )
    
    return _es_client


def _iso_to_dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _index_document(index: str, doc_id: Optional[str], body: dict):
    """Index a document to Elasticsearch"""
    es = _get_es_client()
    if not es:
        print(f"ES client not available; skipping {index} id={doc_id}")
        return
    
    try:
        if doc_id:
            result = es.index(index=index, id=doc_id, document=body)
        else:
            result = es.index(index=index, document=body)
        print(f"Indexed {index} id={doc_id} -> {result.get('result')}")
    except Exception as e:
        print(f"Error indexing {index} id={doc_id}: {type(e).__name__}: {e}")


def _process_event(detail: dict, detail_type: Optional[str] = None):
    if not isinstance(detail, dict):
        print("detail is not a dict, skipping", detail)
        return

    # Determine index name
    index = detail.get("_index") or (detail_type or "event")
    doc_id = detail.get("_id")
    body = detail.get("_source") if "_source" in detail else detail

    # Index the original document
    _index_document(index, doc_id, body)

    try:
        idx_lower = index.lower()
    except Exception:
        idx_lower = ""

    cart_id = body.get("cart_id")

    # ── Scenario 1 & 2: cart_events with add_to_cart → create/update cart_state as "active"
    # Only trigger on cart_events index (not cart_state or other indices containing "cart")
    if idx_lower == "cart_events":
        event_type = (body.get("event_type") or "").lower()
        if event_type == "add_to_cart" and cart_id:
            last_seen = body.get("@timestamp") or body.get("last_seen") or _now_iso()
            try:
                last_seen_dt = _iso_to_dt(last_seen)
            except Exception:
                last_seen_dt = datetime.now(timezone.utc)
            minutes = int(os.getenv("CHECK_AT_MINUTES", "30"))
            check_at_dt = last_seen_dt + timedelta(minutes=minutes)

            cart_state = {
                "@timestamp": _now_iso(),
                "cart_id": cart_id,
                "customer_id": body.get("customer_id"),
                "session_id": body.get("session_id"),
                "last_seen": last_seen,
                "check_at": check_at_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "status": "active",
                "event_type": event_type,
                "cart_value": body.get("cart_value"),
                "currency": body.get("currency"),
                "device_type": body.get("device_type"),
            }

            _index_document("cart_state", f"state_{cart_id}", cart_state)

    # ── Scenario 3: Successful checkout/payment → cart_state "completed"
    if idx_lower in ("checkout_events", "payment_logs"):
        if cart_id:
            status_val = (body.get("status") or "").lower()
            step_val = (body.get("step") or "").lower()
            success = False

            # Common success indicators
            if status_val in ("completed", "success", "succeeded", "paid"):
                success = True
            if step_val in ("completed", "order_completed", "payment_completed"):
                success = True

            # Payment-specific: explicit failed overrides
            if idx_lower == "payment_logs":
                if status_val in ("failed", "error"):
                    success = False
                elif status_val in ("succeeded", "success"):
                    success = True

            if success:
                last_seen = body.get("@timestamp") or _now_iso()
                try:
                    last_seen_dt = _iso_to_dt(last_seen)
                except Exception:
                    last_seen_dt = datetime.now(timezone.utc)
                check_at_dt = datetime.now(timezone.utc)

                cart_state = {
                    "@timestamp": _now_iso(),
                    "cart_id": cart_id,
                    "customer_id": body.get("customer_id"),
                    "session_id": body.get("session_id"),
                    "last_seen": last_seen,
                    "check_at": check_at_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": "completed",
                    "event_type": body.get("event_type") or "checkout",
                    "cart_value": body.get("total") or body.get("cart_value"),
                    "currency": body.get("currency"),
                }

                _index_document("cart_state", f"state_{cart_id}", cart_state)

    # ── Scenario 4: recovery_history event → cart_state "recovery_sent"
    if idx_lower == "recovery_history":
        if cart_id:
            last_seen = body.get("@timestamp") or body.get("sent_at") or _now_iso()
            try:
                last_seen_dt = _iso_to_dt(last_seen)
            except Exception:
                last_seen_dt = datetime.now(timezone.utc)
            check_at_dt = datetime.now(timezone.utc)

            cart_state = {
                "@timestamp": _now_iso(),
                "cart_id": cart_id,
                "customer_id": body.get("customer_id"),
                "last_seen": last_seen,
                "check_at": check_at_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                "status": "recovery_sent",
                "recovery_id": body.get("recovery_id"),
                "action_type": body.get("action", {}).get("type") if isinstance(body.get("action"), dict) else None,
            }

            _index_document("cart_state", f"state_{cart_id}", cart_state)


def lambda_handler(event, context):
    detail = event.get("detail")
    detail_type = event.get("detail-type") or event.get("detailType")

    # If a list of details was provided, iterate
    if isinstance(detail, list):
        for d in detail:
            _process_event(d, detail_type)
        return {"status": "ok", "processed": len(detail)}

    # Single event
    _process_event(detail, detail_type)
    return {"status": "ok"}

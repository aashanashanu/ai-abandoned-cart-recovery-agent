from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException

from src.agent.policies import decide_recovery_action as policy_decide
from src.es.client import build_es_client
from src.models.schemas import (
    AbandonedCartCandidate,
    AnalyzeAbandonmentRequest,
    AnalyzeAbandonmentResponse,
    CustomerProfile,
    DecideRecoveryActionRequest,
    DecideRecoveryActionResponse,
    DetectAbandonedCartsRequest,
    DetectAbandonedCartsResponse,
    FindSimilarAbandonmentsRequest,
    FindSimilarAbandonmentsResponse,
    GetCustomerProfileRequest,
    GetCustomerProfileResponse,
    RecordRecoveryAttemptRequest,
    RecordRecoveryAttemptResponse,
    TriggerRecoveryActionRequest,
    TriggerRecoveryActionResponse,
)


app = FastAPI(title="Abandoned Cart Recovery Tools", version="1.0")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_es_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)


def _es_search(es: Elasticsearch, *, index: str, body: Dict[str, Any]) -> Dict[str, Any]:
    return es.search(index=index, body=body)


def _most_recent_session_id(cart_hits: List[Dict[str, Any]], checkout_hits: List[Dict[str, Any]]) -> Optional[str]:
    for hit in (cart_hits + checkout_hits):
        src = hit.get("_source", {})
        session_id = src.get("session_id")
        if session_id:
            return session_id
    return None


def _diagnose(
    *,
    cart_events: List[Dict[str, Any]],
    checkout_events: List[Dict[str, Any]],
    payment_logs: List[Dict[str, Any]],
    session_metrics: List[Dict[str, Any]],
) -> Dict[str, Any]:
    signals: List[str] = []

    failed_payments = [p for p in payment_logs if p.get("_source", {}).get("status") == "failed"]
    if failed_payments:
        fp = failed_payments[0].get("_source", {})
        if fp.get("failure_code"):
            signals.append(str(fp.get("failure_code")))
        return {
            "root_cause": "payment_failure",
            "signals": signals or ["payment_failed"],
            "evidence": {
                "payment_failure_code": fp.get("failure_code"),
                "payment_failure_message": fp.get("failure_message"),
                "retryable": fp.get("retryable"),
            },
        }

    perf = None
    for m in session_metrics:
        src = m.get("_source", {})
        if src.get("p95_latency_ms") is not None:
            perf = src
            break

    if perf:
        p95 = int(perf.get("p95_latency_ms") or 0)
        apdex = float(perf.get("apdex") or 0.0)
        err = float(perf.get("error_rate") or 0.0)
        if p95 >= 1000 or apdex < 0.85 or err >= 0.05:
            if p95 >= 1000:
                signals.append("high_latency")
            if apdex < 0.85:
                signals.append("low_apdex")
            if err >= 0.05:
                signals.append("high_error_rate")
            return {
                "root_cause": "performance_latency",
                "signals": signals,
                "evidence": {"p95_latency_ms": p95, "apdex": apdex, "error_rate": err},
            }

    shipping_cost = None
    total = None
    for ce in checkout_events:
        src = ce.get("_source", {})
        if src.get("shipping_cost") is not None and src.get("total") is not None:
            shipping_cost = float(src.get("shipping_cost"))
            total = float(src.get("total"))
            break

    if shipping_cost is not None and total and total > 0 and shipping_cost / total >= 0.18:
        return {
            "root_cause": "pricing_shipping",
            "signals": ["high_shipping_cost"],
            "evidence": {"shipping_cost": shipping_cost, "total": total},
        }

    if len(checkout_events) >= 3:
        steps = [c.get("_source", {}).get("step") for c in checkout_events if c.get("_source", {}).get("step")]
        unique_steps = set(steps)
        if "shipping" in unique_steps and "payment" not in unique_steps:
            return {
                "root_cause": "checkout_friction",
                "signals": ["stalled_before_payment"],
                "evidence": {"steps": steps[:10]},
            }

    return {"root_cause": "unknown", "signals": ["insufficient_signals"], "evidence": {}}


@app.on_event("startup")
def _startup() -> None:
    app.state.es = build_es_client()


def _es(app_: FastAPI) -> Elasticsearch:
    es = getattr(app_.state, "es", None)
    if not es:
        raise HTTPException(status_code=500, detail="Elasticsearch client not initialized")
    return es


@app.post(
    "/tools/detect_abandoned_carts",
    operation_id="detect_abandoned_carts",
    response_model=DetectAbandonedCartsResponse,
)
def detect_abandoned_carts(req: DetectAbandonedCartsRequest) -> DetectAbandonedCartsResponse:
    es = _es(app)
    now = _utcnow()
    lookback = now - timedelta(minutes=req.lookback_minutes)

    body: Dict[str, Any] = {
        "size": 0,
        "query": {"bool": {"filter": [{"range": {"@timestamp": {"gte": lookback.isoformat()}}}] }},
        "aggs": {
            "by_cart": {
                "terms": {"field": "cart_id", "size": 1000},
                "aggs": {
                    "last_seen": {"max": {"field": "@timestamp"}},
                    "last_event": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{"@timestamp": {"order": "desc"}}],
                            "_source": {
                                "includes": [
                                    "cart_id",
                                    "customer_id",
                                    "session_id",
                                    "cart_value",
                                    "currency",
                                    "device_type",
                                    "@timestamp",
                                ]
                            },
                        }
                    },
                },
            }
        },
    }

    res = _es_search(es, index="cart_events", body=body)
    buckets = res.get("aggregations", {}).get("by_cart", {}).get("buckets", [])

    candidates: List[AbandonedCartCandidate] = []
    cutoff = now - timedelta(minutes=req.abandonment_minutes)

    for b in buckets:
        last_seen_val = b.get("last_seen", {}).get("value_as_string") or b.get("last_seen", {}).get("value")
        if last_seen_val is None:
            continue
        last_seen = _parse_es_dt(last_seen_val)
        if last_seen > cutoff:
            continue

        last_hit = (
            b.get("last_event", {})
            .get("hits", {})
            .get("hits", [])
        )
        if not last_hit:
            continue

        src = last_hit[0].get("_source", {})
        cart_id = src.get("cart_id")
        customer_id = src.get("customer_id")
        if not cart_id or not customer_id:
            continue

        checkout_done = es.search(
            index="checkout_events",
            size=1,
            query={
                "bool": {
                    "filter": [
                        {"term": {"cart_id": cart_id}},
                        {"term": {"status": "completed"}},
                        {"range": {"@timestamp": {"gte": lookback.isoformat()}}},
                    ]
                }
            },
        )
        if checkout_done.get("hits", {}).get("total", {}).get("value", 0) > 0:
            continue

        candidates.append(
            AbandonedCartCandidate(
                cart_id=cart_id,
                customer_id=customer_id,
                session_id=src.get("session_id"),
                last_seen=last_seen,
                cart_value=float(src.get("cart_value") or 0.0),
                currency=str(src.get("currency") or "USD"),
                device_type=src.get("device_type"),
            )
        )

    candidates.sort(key=lambda c: c.cart_value, reverse=True)
    return DetectAbandonedCartsResponse(candidates=candidates[: req.max_candidates])


@app.post(
    "/tools/analyze_abandonment",
    operation_id="analyze_abandonment",
    response_model=AnalyzeAbandonmentResponse,
)
def analyze_abandonment(req: AnalyzeAbandonmentRequest) -> AnalyzeAbandonmentResponse:
    es = _es(app)

    cart_res = es.search(
        index="cart_events",
        size=50,
        sort=[{"@timestamp": {"order": "desc"}}],
        query={"bool": {"filter": [{"term": {"cart_id": req.cart_id}}]}},
    )
    checkout_res = es.search(
        index="checkout_events",
        size=50,
        sort=[{"@timestamp": {"order": "desc"}}],
        query={"bool": {"filter": [{"term": {"cart_id": req.cart_id}}]}},
    )
    payment_res = es.search(
        index="payment_logs",
        size=25,
        sort=[{"@timestamp": {"order": "desc"}}],
        query={"bool": {"filter": [{"term": {"cart_id": req.cart_id}}]}},
    )

    cart_hits = cart_res.get("hits", {}).get("hits", [])
    checkout_hits = checkout_res.get("hits", {}).get("hits", [])
    payment_hits = payment_res.get("hits", {}).get("hits", [])

    session_id = _most_recent_session_id(cart_hits, checkout_hits)
    session_hits: List[Dict[str, Any]] = []
    if session_id:
        session_res = es.search(
            index="session_metrics",
            size=10,
            sort=[{"@timestamp": {"order": "desc"}}],
            query={"bool": {"filter": [{"term": {"session_id": session_id}}]}},
        )
        session_hits = session_res.get("hits", {}).get("hits", [])

    diagnosis = _diagnose(
        cart_events=cart_hits,
        checkout_events=checkout_hits,
        payment_logs=payment_hits,
        session_metrics=session_hits,
    )

    diagnosis["evidence"] = {
        **diagnosis.get("evidence", {}),
        "checkout_events_count": len(checkout_hits),
        "payment_logs_count": len(payment_hits),
        "session_id": session_id,
    }

    return AnalyzeAbandonmentResponse(cart_id=req.cart_id, diagnosis=diagnosis)  # type: ignore[arg-type]


@app.post(
    "/tools/get_customer_profile",
    operation_id="get_customer_profile",
    response_model=GetCustomerProfileResponse,
)
def get_customer_profile(req: GetCustomerProfileRequest) -> GetCustomerProfileResponse:
    es = _es(app)

    try:
        doc = es.get(index="customer_profiles", id=req.customer_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=404, detail=f"Customer not found: {req.customer_id}") from e

    src = doc.get("_source", {})
    profile = CustomerProfile(
        customer_id=src.get("customer_id", req.customer_id),
        email=src.get("email"),
        phone=src.get("phone"),
        push_token=src.get("push_token"),
        segment=src.get("segment", "standard"),
        lifetime_value=float(src.get("lifetime_value") or 0.0),
        preferred_channel=src.get("preferred_channel", "email"),
        fraud_risk=src.get("fraud_risk", "low"),
        locale=src.get("locale"),
        timezone=src.get("timezone"),
    )

    return GetCustomerProfileResponse(profile=profile)


@app.post(
    "/tools/find_similar_abandonments",
    operation_id="find_similar_abandonments",
    response_model=FindSimilarAbandonmentsResponse,
)
def find_similar_abandonments(req: FindSimilarAbandonmentsRequest) -> FindSimilarAbandonmentsResponse:
    es = _es(app)

    now = _utcnow()
    lookback = now - timedelta(days=req.lookback_days)

    cart_value = float(req.similarity.cart_value)
    low = max(0.0, cart_value * 0.8)
    high = cart_value * 1.2 if cart_value > 0 else 999999

    body: Dict[str, Any] = {
        "size": req.size,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"diagnosis.root_cause": req.similarity.root_cause}},
                    {"term": {"segment": req.similarity.segment}},
                    {"range": {"cart_value": {"gte": low, "lte": high}}},
                    {"range": {"@timestamp": {"gte": lookback.isoformat()}}},
                ]
            }
        },
        "aggs": {
            "by_action": {
                "terms": {"field": "action.type", "size": 10},
                "aggs": {
                    "by_outcome": {"terms": {"field": "outcome.status", "size": 10}},
                    "avg_recovered": {"avg": {"field": "outcome.revenue_recovered"}},
                },
            }
        },
        "sort": [{"@timestamp": {"order": "desc"}}],
    }

    res = _es_search(es, index="recovery_history", body=body)

    stats = []
    for b in res.get("aggregations", {}).get("by_action", {}).get("buckets", []):
        total = int(b.get("doc_count") or 0)
        outcomes = {o.get("key"): int(o.get("doc_count") or 0) for o in b.get("by_outcome", {}).get("buckets", [])}
        recovered = int(outcomes.get("recovered", 0))
        success_rate = (recovered / total) if total > 0 else 0.0
        avg_recovered = float(b.get("avg_recovered", {}).get("value") or 0.0)

        stats.append(
            {
                "action_type": b.get("key"),
                "total": total,
                "recovered": recovered,
                "success_rate": success_rate,
                "avg_revenue_recovered": avg_recovered,
            }
        )

    examples = [h.get("_source", {}) for h in res.get("hits", {}).get("hits", [])]

    return FindSimilarAbandonmentsResponse(stats=stats, examples=examples)  # type: ignore[arg-type]


@app.post(
    "/tools/decide_recovery_action",
    operation_id="decide_recovery_action",
    response_model=DecideRecoveryActionResponse,
)
def decide_recovery_action(req: DecideRecoveryActionRequest) -> DecideRecoveryActionResponse:
    decision = policy_decide(
        cart=req.cart,
        diagnosis=req.diagnosis,
        customer=req.customer,
        similar_stats=req.similar_stats,
    )
    return DecideRecoveryActionResponse(action=decision.action, rationale=decision.rationale)


@app.post(
    "/tools/trigger_recovery_action",
    operation_id="trigger_recovery_action",
    response_model=TriggerRecoveryActionResponse,
)
def trigger_recovery_action(req: TriggerRecoveryActionRequest) -> TriggerRecoveryActionResponse:
    action = req.action
    customer = req.customer

    if action.channel == "email" and not customer.email:
        return TriggerRecoveryActionResponse(status="skipped")
    if action.channel == "sms" and not customer.phone:
        return TriggerRecoveryActionResponse(status="skipped")
    if action.channel == "push" and not customer.push_token:
        return TriggerRecoveryActionResponse(status="skipped")

    message_id = f"msg_{uuid.uuid4().hex[:12]}"
    return TriggerRecoveryActionResponse(status="sent", message_id=message_id, channel=action.channel)


@app.post(
    "/tools/record_recovery_attempt",
    operation_id="record_recovery_attempt",
    response_model=RecordRecoveryAttemptResponse,
)
def record_recovery_attempt(req: RecordRecoveryAttemptRequest) -> RecordRecoveryAttemptResponse:
    es = _es(app)

    recovery_id = f"rec_{uuid.uuid4().hex}"

    doc = {
        "@timestamp": _utcnow().isoformat(),
        "recovery_id": recovery_id,
        "cart_id": req.cart.cart_id,
        "customer_id": req.customer.customer_id,
        "segment": req.customer.segment,
        "cart_value": req.cart.cart_value,
        "currency": req.cart.currency,
        "diagnosis": {
            "root_cause": req.diagnosis.root_cause,
            "signals": req.diagnosis.signals,
        },
        "action": {
            "type": req.action.type,
            "channel": req.action.channel,
            "discount_percent": req.action.discount_percent,
            "free_shipping": req.action.free_shipping,
            "template": req.action.template,
        },
        "sent_at": req.sent_at.isoformat(),
        "outcome": {"status": "pending"},
    }

    es.index(index="recovery_history", id=recovery_id, document=doc)
    return RecordRecoveryAttemptResponse(recovery_id=recovery_id)

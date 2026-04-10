# Project Documentation

## Overview

The AI Abandoned Cart Recovery Agent is an event-driven system built on
**AWS** (EventBridge, Lambda, API Gateway, SES, S3) and **Elasticsearch**
(indices, scheduled workflows, AI Agent). It detects abandoned carts, diagnoses
why they were abandoned, and uses an AI agent with MCP tools to execute
personalised recovery actions.

---

## Architecture Summary

```
Events → EventBridge → Event Ingest Lambda → Elasticsearch (7 indices + cart_state)
                                                      │
                                    Scheduled Workflow (every 5 min)
                                                      │
                                              AI Agent (MCP tools)
                                                      │
                                    ┌─────────────────┴──────────────────┐
                                    ▼                                    ▼
                            Decision Engine                      Recovery Action
                            (S3 matrix)                          (SES + EventBridge)
```

See [architecture_diagram.md](architecture_diagram.md) for the full diagram.

---

## 1. Event Ingestion

### EventBridge → Lambda → Elasticsearch

The seed script (`scripts/seed_sample_data.py`) and production systems emit
events to **Amazon EventBridge** via `PutEvents`. An EventBridge rule triggers
the **Event Ingest Lambda** (`aws/lambda/event_ingest/handler.py`).

The Lambda:
- Indexes the event document into the correct Elasticsearch index
- Creates or updates a `cart_state` document per cart:
  - `add_to_cart` → creates state as `active` with `check_at` = now + 30 min
  - Successful checkout/payment → marks state as `completed`
  - `recovery_history` → marks state as `recovery_sent`

### Event Types

| Source field `_index` | Elasticsearch Index | Purpose |
|-----------------------|---------------------|---------|
| `customer_profiles` | `customer_profiles` | Customer segment, fraud risk, contact info |
| `cart_events` | `cart_events` | Cart activity (add_to_cart) |
| `checkout_events` | `checkout_events` | Checkout progress and failures |
| `payment_logs` | `payment_logs` | Payment attempt outcomes |
| `session_metrics` | `session_metrics` | Page latency and error rates |
| `recovery_history` | `recovery_history` | Past recovery actions and outcomes |
| *(derived)* | `cart_state` | Per-cart state managed by Lambda |

---

## 2. Elasticsearch Indices

### Mappings (`elastic/mappings/`)

| Index | Key Fields |
|-------|-----------|
| `cart_events` | cart_id, customer_id, session_id, event_type, product_id, quantity, unit_price, cart_value, currency, device_type, page, referrer |
| `checkout_events` | checkout_id, cart_id, customer_id, session_id, step, status, shipping_method, payment_method, shipping_cost, tax, total, currency |
| `customer_profiles` | customer_id, email, phone, push_token, segment, lifetime_value, preferred_channel, fraud_risk, locale, timezone |
| `payment_logs` | payment_id, checkout_id, cart_id, customer_id, provider, status, failure_code, failure_message, retryable, gateway_latency_ms |
| `session_metrics` | session_id, customer_id, p95_latency_ms, error_rate, page_views, device_type, browser |
| `recovery_history` | recovery_id, cart_id, customer_id, segment, cart_value, diagnosis, action, outcome |
| `cart_state` | cart_id, customer_id, status, cart_value, currency, device_type, session_id, last_seen, check_at |

### Queries (`elastic/queries/`)

Standalone query examples for ad-hoc analysis:

| File | Purpose |
|------|---------|
| `detect_abandoned_carts.json` | Find carts idle 30+ min |
| `analyze_abandonment_cart_checkout.json` | Checkout events for a cart |
| `analyze_abandonment_payment_logs.json` | Payment failures for a cart |
| `find_similar_abandonments.json` | Historical similar cases |

> **Note**: The workflow embeds its own queries inline. These files are for
> reference and ad-hoc use in Kibana Dev Tools.

---

## 3. Scheduled Workflow

**File**: `elastic/workflows/detect_abandonment_reasons.yml`

Runs every **5 minutes** inside Elasticsearch.

### Steps

| # | Step Name | Type | Description |
|---|-----------|------|-------------|
| 1 | `find_abandoned_carts` | `elasticsearch.search` | Query `cart_state` for `status=active` AND `check_at < now`, up to 100 carts |
| 2 | `extract_cart_data` | `data.set` | Extract `hits → _source` into iterable `carts` array |
| 3 | `conditionalStep` | `if` | Only proceed if `carts.length > 0` |
| 3a | `for_each_cart` | `foreach` | Iterate over each abandoned cart |

### Per-Cart Sub-Steps

| Step | Type | Details |
|------|------|---------|
| `fetch_customer_profile` | `elasticsearch.search` | `customer_profiles` by `customer_id` |
| `fetch_cart_events` | `elasticsearch.search` | `cart_events` by `cart_id` (size 10) |
| `fetch_latest_checkout` | `elasticsearch.search` | `checkout_events` by `cart_id` (size 1) |
| `fetch_latest_payment` | `elasticsearch.search` | `payment_logs` by `cart_id` (size 1) |
| `fetch_session_metrics` | `elasticsearch.search` | `session_metrics` by `session_id` (size 1) |

### Root Cause Diagnosis

Five conditional branches, first match wins via Liquid `if/elsif`:

| Branch | Condition | Root Cause |
|--------|-----------|-----------|
| `decide_payment_failure` | Payment exists AND `status = "failed"` | `payment_failure` |
| `decide_checkout_shipping` | Checkout exists AND `step = "shipping_failed"` | `pricing_shipping` |
| `decide_performance` | Session metrics AND (`p95 > 1000ms` OR `error_rate > 5%`) | `performance_latency` |
| `decide_browse` | Cart events AND no checkout events | `browsing_or_window_shopping` |
| `decide_unknown` | No payment, no checkout, no session data | `unknown` |

### Final Diagnosis Payload

```json
{
  "cart_id": "...",
  "customer_id": "...",
  "cart_value": 229.0,
  "currency": "USD",
  "device_type": "mobile",
  "last_seen": "...",
  "session_id": "...",
  "check_at": "...",
  "customer_profile": {
    "segment": "vip",
    "lifetime_value": 5000.0,
    "preferred_channel": "email",
    "fraud_risk": "low",
    "email": "alex@example.com",
    "phone": "+155555501"
  },
  "final_diagnosis": {
    "root_cause": "payment_failure",
    "signals": ["declined_insufficient_funds", "Card declined"]
  }
}
```

### AI Agent Call

| Field | Value |
|-------|-------|
| Type | `ai.agent` |
| Agent ID | `abandoned_cart` |
| Input | Full `emit_final_diagnosis` payload |

The agent calls two MCP tools in sequence:
1. **`decision_engine`** — determines recommended action
2. **`recovery_action`** — sends recovery email and logs history

See [serverless_workflow_diagram.md](serverless_workflow_diagram.md) for
detailed flow diagrams.

---

## 4. MCP Server & Tools

### Architecture

```
Elastic AI Agent
       │  Streamable HTTP (JSON-RPC 2.0)
       │  x-api-key header
       ▼
API Gateway (POST /mcp)
       │
       ▼
MCP Server Lambda (JSON-RPC router)
       │
  ┌────┴─────┐
  ▼          ▼
Decision   Recovery
Engine     Action
Lambda     Lambda
```

See [aws/MCP_SERVER.md](../aws/MCP_SERVER.md) for full details.

### Tool Definitions (`elastic/tools/`)

| File | Purpose |
|------|---------|
| `mcp_server.yml` | MCP server config (URL, API key, protocol version, tool list) |
| `decision_engine.yml` | Tool schema — input params and output for decision engine |
| `recovery_action.yml` | Tool schema — input params and output for recovery action |

### Decision Engine Lambda

**File**: `aws/lambda/decision_engine/handler.py`

- Reads `decision-matrix.json` from S3
- Resolves action by matching: customer segment → abandonment reason → cart value
- High-cart-value overrides (VIP > $500, Standard > $300 → discount)
- Returns: `{ type, discount, message, free_shipping }`

### Recovery Action Lambda

**File**: `aws/lambda/recovery_action/handler.py`

- Builds HTML/text email from action type and message
- Sends email via **Amazon SES**
- Publishes `recovery_history` event to **EventBridge** (feedback loop)
- Returns: `{ recovery_id, action_taken, send_result: { status, channel, message_id } }`

---

## 5. Decision Matrix

**File**: `aws/decision-matrix/decision-matrix.json`

Action rules by customer segment:

| Segment | Reason | Action |
|---------|--------|--------|
| VIP | payment_failure | payment_retry |
| VIP | shipping_issue | free_shipping |
| VIP | cart_value > $500 | discount 15% |
| VIP | default | free_shipping |
| Standard | payment_failure | payment_retry |
| Standard | shipping_issue | free_shipping |
| Standard | cart_value > $300 | discount 10% |
| Standard | default | reminder |
| High Fraud Risk | payment_failure | blocked |
| High Fraud Risk | default | reminder_only |

---

## 6. Scripts

### `scripts/bootstrap_indices.py`

Creates Elasticsearch indices from mapping files in `elastic/mappings/`.
Skips indices that already exist.

### `scripts/seed_sample_data.py`

Generates sample events and sends them to EventBridge via `PutEvents`:
- 5 customer profiles (VIP, standard ×3, high_fraud_risk)
- Cart events for 5 scenarios
- Checkout events (payment_failed, shipping_failed)
- Payment logs (failed, completed)
- Session metrics with varying latency/error rates
- Recovery history from past attempts

The Event Ingest Lambda picks these up and indexes them into Elasticsearch.

---

## 7. AWS Resources

Deployed via `aws/stack.yml` (CloudFormation/SAM):

| Resource | Description |
|----------|-------------|
| EventBridge Bus | Custom event bus for all cart events |
| Event Ingest Lambda | Indexes events into Elasticsearch |
| Decision Engine Lambda | Reads S3 matrix, returns action |
| Recovery Action Lambda | Sends SES email, publishes history |
| MCP Server Lambda | JSON-RPC 2.0 router for MCP tools |
| API Gateway | Public HTTPS endpoint with API key auth |
| S3 Bucket | Stores `decision-matrix.json` |

---

## 8. Deployment

### AWS

```bash
cd aws && ./deploy.sh dev
```

See [aws/DEPLOY.md](../aws/DEPLOY.md) for full instructions.

### Elasticsearch

```bash
python scripts/bootstrap_indices.py   # Create indices
python scripts/seed_sample_data.py    # Seed data via EventBridge
```

Import workflow in Kibana: **Stack Management → Workflows → Import** →
`elastic/workflows/detect_abandonment_reasons.yml`

### AI Agent

Create agent in **AI Assistants → Agent Builder** with ID `abandoned_cart`.
Add the MCP Server connector using the URL and API key from deployment output.

---

## 9. Troubleshooting

### Events not appearing in Elasticsearch
- Check `EVENT_BUS_NAME` env var matches deployed bus
- Check Event Ingest Lambda CloudWatch logs
- Verify `ES_ENDPOINT` and `ES_API_KEY` are set in Lambda env

### Workflow not finding abandoned carts
- Verify `cart_state` index has documents with `status: active`
- Check `check_at` values are in the past
- Run `GET cart_state/_search` in Kibana Dev Tools

### MCP tools not responding
- Test health: `curl $MCP_SERVER_URL -H "x-api-key: $KEY"`
- Check MCP Server Lambda logs
- Verify Decision Engine and Recovery Action Lambdas exist

### Recovery emails not sending
- Verify `SENDER_EMAIL` is set and verified in SES
- Check SES sandbox mode (may need to verify recipient too)
- Check Recovery Action Lambda logs

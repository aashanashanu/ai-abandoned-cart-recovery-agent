# Requirements Analysis

Analysis of how the Abandoned Cart Recovery Agent meets the specified requirements.

---

## Requirement: Multi-Step AI Agent

**Status**: Met

The system chains multiple automated steps:

1. **EventBridge → Lambda** ingests events and indexes them into Elasticsearch,
   maintaining per-cart state.
2. **Scheduled Workflow** (`detect_abandonment_reasons`) runs every 5 min in
   Elasticsearch with nested steps:
   - `elasticsearch.search` to find abandoned carts
   - `foreach` loop with 5 data-fetch queries per cart
   - 5 conditional diagnosis branches (Liquid `if/elsif`)
   - `data.set` to consolidate the final diagnosis
3. **Elastic AI Agent** (`ai.agent` step) receives the diagnosis payload.
4. Agent calls **two MCP tools** in sequence: `decision_engine` then
   `recovery_action`.
5. Recovery Action publishes a `recovery_history` event back to EventBridge,
   closing the feedback loop.

---

## Requirement: Reasoning Model Integration

**Status**: Met

The Elastic AI Agent receives a structured diagnosis payload and must:
- Parse the root cause and customer profile
- Decide which MCP tool parameters to use
- Call `decision_engine` first, then pass its output to `recovery_action`
- Summarise the complete recovery in a structured response schema

The workflow itself applies rule-based reasoning via Liquid templating to
diagnose the root cause from five possible branches.

---

## Requirement: Multiple Tool Types

**Status**: Met

| Tool Type | Usage |
|-----------|-------|
| `elasticsearch.search` | 6 queries per cart iteration (cart_state, customer_profiles, cart_events, checkout_events, payment_logs, session_metrics) |
| `data.set` | Extract cart array, set diagnosis, emit final payload |
| `if` / `elsif` | 5 conditional branches for root-cause diagnosis |
| `foreach` | Iterate over abandoned carts |
| `ai.agent` | Call Elastic AI Agent with diagnosis payload |
| MCP tool: `decision_engine` | Lambda reads S3 decision matrix, returns recommended action |
| MCP tool: `recovery_action` | Lambda sends SES email and publishes EventBridge event |
| AWS Lambda | Event Ingest, Decision Engine, Recovery Action, MCP Server |
| Amazon EventBridge | Event bus for ingestion and recovery history feedback loop |
| Amazon SES | Email delivery |
| Amazon S3 | Decision matrix storage |
| API Gateway | MCP Server endpoint with API key auth |

---

## Requirement: Real-World Task Automation

**Status**: Met

The system automates the complete abandoned cart recovery lifecycle:

| Phase | Implementation |
|-------|---------------|
| **Detection** | Scheduled workflow queries `cart_state` every 5 min |
| **Data enrichment** | Fetches customer profile, cart history, checkout, payment, session data |
| **Diagnosis** | Five root-cause branches with signal extraction |
| **Decision** | AI Agent → Decision Engine (segment + reason + value + fraud → action) |
| **Execution** | AI Agent → Recovery Action (SES email delivery) |
| **Tracking** | Recovery history indexed via EventBridge → Lambda → Elasticsearch |
| **Loop closure** | `cart_state` updated to `recovery_sent`, preventing duplicates |

---

## Requirement: Real-World Applicability

**Status**: Met

Production-ready features:

- **Event-driven architecture** — EventBridge decouples producers from consumers
- **Idempotent ingestion** — Documents indexed by deterministic IDs
- **Fraud guardrails** — High-risk customers get `reminder_only` or `blocked`
- **Cart value thresholds** — VIP > $500 and Standard > $300 trigger discounts
- **Feedback loop** — Recovery history prevents duplicate recovery attempts
- **API key security** — MCP Server secured via API Gateway API key
- **Throttling** — 100 req/s, 10,000 req/day quota on MCP endpoint
- **Observability** — CloudWatch logs for all Lambdas, recovery_history index for analytics

---

## Compliance Summary

| Requirement | Status | Key Evidence |
|-------------|--------|-------------|
| Multi-Step AI Agent | **Met** | EventBridge → Lambda → ES → Workflow (6 queries + 5 conditions per cart) → AI Agent → 2 MCP tools |
| Reasoning Model Integration | **Met** | Elastic AI Agent interprets diagnosis, chains MCP tool calls, returns structured response |
| Multiple Tool Types | **Met** | ES search, data.set, if/foreach, ai.agent, MCP tools, Lambda, EventBridge, SES, S3, API GW |
| Real-World Task Automation | **Met** | End-to-end: detection → diagnosis → decision → email delivery → history tracking |
| Real-World Applicability | **Met** | Event-driven, idempotent, fraud guardrails, feedback loop, API security, observability |

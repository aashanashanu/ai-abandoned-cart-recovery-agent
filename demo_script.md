# 3-Minute Demo Script

## Opening (15 seconds)

> "I'll show you an intelligent abandoned cart recovery system. Events flow
> through EventBridge into Elasticsearch, a scheduled workflow detects
> abandoned carts every 5 minutes, and an AI agent calls MCP tools to decide
> the best recovery action and send the email — all automated."

---

## Step 1 — Seed Data (30 seconds)

> "First, we send sample events to EventBridge. The Event Ingest Lambda
> indexes them into Elasticsearch and creates cart_state documents."

```bash
python scripts/seed_sample_data.py
```

Expected output:
```
Enhanced sample data events sent to EventBridge: attempted=33 accepted=33
Generated 5 customer profiles
Generated 10 cart events
Generated 4 checkout events
Generated 2 payment logs
Generated 5 session metrics
Generated 6 recovery history entries

=== Test Scenarios Created ===
1. cart_1001: VIP customer with payment failure -> payment_retry
2. cart_2002: Standard customer with shipping cost -> free_shipping
3. cart_3003: New customer with performance issues -> reminder
4. cart_4004: High fraud risk customer -> reminder (guardrail)
5. cart_5005: International customer -> based on history
```

---

## Step 2 — Verify Indexing (15 seconds)

> "Let's confirm the data landed in Elasticsearch."

In Kibana Dev Tools:
```
GET _cat/indices/cart_state,cart_events,customer_profiles,checkout_events,payment_logs,session_metrics?v&h=index,docs.count
```

Expected: `cart_state` has 5 documents (one per cart), all with
`status: active`.

---

## Step 3 — Workflow Triggers (1 minute)

> "The `detect_abandonment_reasons` workflow runs every 5 minutes. It queries
> cart_state for active carts past their check_at time, fetches related data
> from all indices, diagnoses the root cause, and calls the AI agent."

Show the workflow in Kibana: **Stack Management → Workflows →
detect_abandonment_reasons**

Key points to highlight:
1. **Step 1**: Queries `cart_state` where `status=active` AND `check_at < now`
2. **Foreach loop**: Processes each cart individually
3. **5 data fetches**: customer_profiles, cart_events, checkout_events,
   payment_logs, session_metrics
4. **5 diagnosis branches**: payment_failure → pricing_shipping →
   performance_latency → browsing_or_window_shopping → unknown
5. **AI Agent call**: Passes full diagnosis to agent `abandoned_cart`

> "The agent then calls two MCP tools in sequence."

---

## Step 4 — MCP Tools (30 seconds)

> "The AI agent calls the Decision Engine to get the recommended action, then
> calls Recovery Action to send the email and log the history."

Show MCP Server health check:
```bash
curl https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl'
```

Show available tools:
```bash
curl -X POST https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

---

## Step 5 — Verify Results (30 seconds)

> "After the workflow completes, recovery_history has new entries and
> cart_state is updated to recovery_sent."

In Kibana Dev Tools:
```
GET recovery_history/_search?sort=@timestamp:desc&size=5
```

Verify each scenario got the expected action:

| Cart | Customer | Diagnosis | Expected Action |
|------|----------|-----------|----------------|
| cart_1001 | cust_001 (VIP) | payment_failure | payment_retry |
| cart_2002 | cust_002 (standard) | pricing_shipping | free_shipping |
| cart_3003 | cust_004 (standard, $410) | performance_latency or browsing | discount 10% or reminder |
| cart_4004 | cust_003 (high_fraud_risk) | payment_failure | blocked |
| cart_5005 | cust_005 (standard) | pricing_shipping | free_shipping |

Check cart_state was updated:
```
GET cart_state/_search?q=status:recovery_sent
```

---

## Closing (15 seconds)

> "The system runs fully autonomously. Events flow through EventBridge, get
> indexed by Lambda, the scheduled workflow detects abandoned carts, the AI
> agent diagnoses each one, calls the Decision Engine for the best action, and
> sends the recovery email — all within minutes of cart abandonment. Recovery
> history feeds back through EventBridge, closing the loop."

**Key takeaways**:
- Event-driven: EventBridge → Lambda → Elasticsearch
- Scheduled detection: Workflow runs every 5 minutes
- AI-powered: Elastic AI Agent with MCP tools
- Feedback loop: Recovery history prevents duplicate attempts
- Fraud guardrails: High-risk customers are blocked or reminder-only

**Total time**: ~3 minutes

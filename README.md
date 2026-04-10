# AI Abandoned Cart Recovery Agent

An event-driven system that detects abandoned shopping carts and triggers
personalised recovery actions using **AWS EventBridge + Lambda**,
**Elasticsearch**, an **Elastic AI Agent**, and two **MCP tools**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

| Category | Detail |
|----------|--------|
| **Event-Driven Ingestion** | All e-commerce signals (cart activity, checkout progress, payment attempts, session performance, customer profiles) are emitted to Amazon EventBridge. An Event Ingest Lambda consumes every event and indexes it into the correct Elasticsearch index in real time. |
| **Automatic Cart-State Management** | The ingest Lambda derives and maintains a `cart_state` document per cart, tracking its lifecycle: `active` → `completed` → `recovery_sent`. This state drives the detection workflow and prevents duplicate recovery attempts. |
| **Scheduled Abandonment Detection** | A workflow inside Elasticsearch runs every 5 minutes, querying `cart_state` for carts that have been active beyond their `check_at` window (default 30 min). Up to 100 carts are processed per cycle. |
| **Multi-Signal Root-Cause Diagnosis** | For each abandoned cart the workflow fetches data from 5 indices and evaluates 5 conditional branches in priority order: payment failure → shipping/pricing issue → performance/latency → pure browsing → unknown. |
| **Elastic AI Agent Integration** | An `ai.agent` workflow step hands the full diagnosis payload to the `abandoned_cart` Elastic AI Agent, which autonomously decides how to recover the cart using natural language reasoning. |
| **MCP Tool Architecture** | The AI Agent connects to an MCP (Model Context Protocol) Server over Streamable HTTP (JSON-RPC 2.0) with API-key auth, calling two tools in sequence: Decision Engine and Recovery Action. |
| **Rules-Based Decision Engine** | A Lambda reads a JSON decision matrix from S3 and resolves the optimal action (payment retry, discount, free shipping, reminder, or blocked) based on customer segment, abandonment reason, cart value, and fraud risk. High-value carts automatically trigger discounts (VIP > $500 → 15 %, Standard > $300 → 10 %). |
| **Multi-Channel Recovery Action** | A Lambda sends a branded HTML email via Amazon SES, then publishes a `recovery_history` event back to EventBridge — closing the feedback loop so the cart is marked `recovery_sent` and analytics stay up to date. |
| **Fraud Guardrails** | High-fraud-risk customers are automatically blocked from financial incentives. Payment failures for high-risk accounts produce a `blocked` action; all other reasons produce `reminder_only`. |
| **Full Observability** | Every Lambda writes structured logs to CloudWatch. Recovery outcomes are stored in the `recovery_history` index for Kibana dashboards — recovery rate by action, conversion by segment, revenue recovered. |
| **One-Command Deployment** | The entire AWS stack (EventBridge bus, 4 Lambdas, API Gateway, S3 bucket, IAM roles) deploys via a single `./deploy.sh dev` script using CloudFormation/SAM. |

---

## Agent Overview

The AI Abandoned Cart Recovery Agent is an autonomous, event-driven system that
closes the gap between cart abandonment and revenue recovery. Rather than
relying on batch jobs and generic discount blasts, it operates as a continuous
pipeline:

1. **Ingestion** — Every cart, checkout, payment, and session event flows through
   EventBridge into Elasticsearch within seconds of occurring.
2. **Detection** — A scheduled workflow polls for carts whose inactivity window
   has expired, processes up to 100 per cycle, and enriches each with customer
   profile and session data.
3. **Diagnosis** — Five rule-based branches inspect payment logs, checkout
   failures, session latency, and browsing patterns to determine *why* the cart
   was abandoned — not just *that* it was abandoned.
4. **Decision** — An Elastic AI Agent receives the diagnosis and calls the
   Decision Engine MCP tool, which matches the cart against a segment-aware
   decision matrix stored in S3.
5. **Action** — The agent then calls the Recovery Action MCP tool, which sends a
   personalised email via SES and publishes a tracking event back to
   EventBridge.
6. **Feedback** — The recovery event is re-ingested by the same Lambda, updating
   `cart_state` to `recovery_sent` so the cart is never processed twice.

The agent runs fully autonomously — no human intervention is required once the
workflow is enabled.

---

## Problem Solved

Abandoned carts cost the e-commerce industry an estimated **$260 billion** in
recoverable revenue each year. Traditional recovery systems suffer from three
fundamental problems:

| Problem | How This Agent Solves It |
|---------|------------------------|
| **Generic discount blasts** — every customer gets the same 10 % coupon regardless of why they left. | The agent diagnoses the *root cause* (payment failure, shipping cost, latency, browsing) and selects the least-costly, most-effective action per scenario. VIPs get payment retries or free shipping, not blanket discounts. |
| **Batch processing delay** — recovery emails fire hours or days later, when intent has evaporated. | Events flow through EventBridge in real time; the workflow runs every 5 minutes. Recovery emails land within minutes of abandonment. |
| **No fraud protection** — discounts go to everyone, including high-risk accounts that may be testing stolen cards. | High-fraud-risk customers are automatically blocked from receiving financial incentives. The decision matrix enforces guardrails before any email is sent. |
| **No feedback loop** — recovery attempts are fire-and-forget with no tracking. | Every recovery action publishes a `recovery_history` event back to EventBridge, updating the cart state and building an analytics trail for Kibana dashboards. |

---

## Features Used

### Elastic Platform

| Feature | How It's Used |
|---------|--------------|
| **Elasticsearch Indices** | 7 indices (`cart_events`, `checkout_events`, `payment_logs`, `customer_profiles`, `session_metrics`, `cart_state`, `recovery_history`) store all event data with strict mappings. |
| **Elasticsearch Workflows** | The `detect_abandonment_reasons` workflow uses `elasticsearch.search`, `data.set`, `if`, `foreach`, and `ai.agent` step types to orchestrate the full detection-to-recovery pipeline on a 5-minute schedule. |
| **Liquid Templating** | Dynamic content transformation inside the workflow — `if/elsif` chains select the winning diagnosis, `map` extracts `_source` arrays, and interpolation passes data into the AI agent prompt. |
| **Elastic AI Agent (Agent Builder)** | The `abandoned_cart` agent receives a structured diagnosis payload and autonomously chains two MCP tool calls, returning a structured JSON response with decision and recovery results. |

### AWS Services

| Service | How It's Used |
|---------|--------------|
| **Amazon EventBridge** | Custom event bus receives all e-commerce events (PutEvents, batches of 10). An EventBridge rule triggers the Event Ingest Lambda on every event. |
| **AWS Lambda (×4)** | Event Ingest indexes events + manages `cart_state`. Decision Engine reads S3 matrix. Recovery Action sends SES email + publishes history. MCP Server routes JSON-RPC calls to the other two Lambdas. |
| **Amazon S3** | Stores the `decision-matrix.json` — a segment/reason/value lookup table the Decision Engine Lambda reads on every invocation. |
| **Amazon SES** | Sends branded HTML recovery emails with dynamic subject lines, discount badges, and CTA buttons. |
| **API Gateway** | Provides a public HTTPS endpoint (`POST /mcp`) for the MCP Server Lambda, secured with an API key and usage plan (100 req/s, 10 000/day). |
| **CloudFormation / SAM** | The entire stack (bus, rules, Lambdas, API Gateway, S3, IAM) is defined in a single `stack.yml` and deployed via `deploy.sh`. |

### MCP (Model Context Protocol)

| Component | Detail |
|-----------|--------|
| **Transport** | Streamable HTTP (JSON-RPC 2.0) over HTTPS |
| **Authentication** | API Gateway API key (`x-api-key` header) |
| **Protocol version** | `2025-03-26` |
| **Tools exposed** | `decision_engine` (read-only, returns action) and `recovery_action` (side-effect, sends email + publishes event) |
| **Methods** | `initialize`, `ping`, `tools/list`, `tools/call`, `notifications/initialized` |

---

## Key Highlights

1. **End-to-end autonomy** — From the moment a cart event hits EventBridge to the
   recovery email landing in the customer's inbox, no human touches the process.
   The workflow, AI agent, and MCP tools handle everything.

2. **Root-cause-first approach** — Instead of asking "has this cart been idle?",
   the system asks "*why* was it abandoned?". Five diagnostic branches inspect
   payment failures, shipping friction, page latency, and browsing patterns to
   select the right recovery lever.

3. **Segment-aware decision matrix** — The JSON matrix in S3 encodes different
   strategies per customer segment (VIP, Standard, High Fraud Risk). VIPs get
   payment retries and free shipping; standard customers get reminders and
   smaller discounts; high-risk accounts get blocked or reminder-only.

4. **Closed feedback loop** — Recovery Action publishes a `recovery_history`
   event back to EventBridge → the same Event Ingest Lambda picks it up →
   updates `cart_state` to `recovery_sent`. This prevents duplicate emails and
   feeds analytics dashboards.

5. **MCP as the AI-to-action bridge** — The Elastic AI Agent doesn't make HTTP
   calls or query databases directly. It calls well-defined MCP tools with
   typed schemas, keeping the agent prompt clean and the action layer testable
   independently.

6. **Single-command deployment** — `./deploy.sh dev` packages and deploys the
   CloudFormation stack including all four Lambdas, EventBridge bus, API
   Gateway, S3 bucket, IAM roles, and the decision matrix — in under 3 minutes.

7. **Idempotent ingestion** — Documents are indexed by deterministic IDs
   (`state_{cart_id}`, `rec_{uuid}`), so replayed events overwrite rather than
   duplicate.

---

## Development Challenges

### 1. Cart-State Lifecycle Management

The hardest problem was deriving a reliable `cart_state` from a stream of
independent events. A single cart can generate multiple `add_to_cart` events,
followed by checkout and payment events that arrive out of order. The solution
was to use upserts on a deterministic document ID (`state_{cart_id}`) and let
the Lambda decide the transition: `active` (on add_to_cart), `completed` (on
successful checkout or payment), or `recovery_sent` (on recovery_history). Each
transition sets `check_at` to control when the workflow picks the cart up.

### 2. Diagnosis Priority Ordering

Multiple diagnostic branches can match the same cart. For example, a cart might
have both a failed payment *and* high session latency. Getting the priority
right (`payment_failure` wins over `performance_latency`) required careful
ordering of the Liquid `if/elsif` chain and extensive testing across all five
scenario combinations.

### 3. Workflow ↔ AI Agent Data Handoff

The `ai.agent` step receives the diagnosis as a Liquid-interpolated string
inside a prompt. Ensuring the payload was valid JSON after interpolation — with
nested objects, arrays, and edge cases like `null` values — required escaping
and the `| json` filter. Debugging Liquid rendering issues inside an
Elasticsearch workflow has no "step debugger", so validation relied on
inspecting the recovery_history output.

### 4. MCP Server Lambda Cold Starts

The MCP Server Lambda invokes two other Lambdas synchronously
(`lambda:InvokeFunction`). In cold-start scenarios this stacks three cold
starts (MCP → Decision Engine → Recovery Action). The mitigation was keeping
Lambda memory at 256 MB for fast init and enabling the
`event_ingest` Lambda to keep the Elasticsearch client as a module-level
singleton for warm invocations.

### 5. Decision Matrix Flexibility vs. Complexity

The S3-based decision matrix needed to support segment-level defaults,
per-reason overrides, and cart-value thresholds — all in a flat JSON file. The
`resolve_action` function in the Decision Engine walks the matrix in a specific
order: check high-cart-value override → check reason-specific rule → fall back
to default segment → fall back to global default. Keeping this deterministic
across VIP, Standard, and High Fraud Risk segments required careful unit-test
coverage.

---

## Key Takeaways

1. **Event-driven beats polling.** Piping all events through EventBridge and
   deriving state in a Lambda (rather than polling Elasticsearch directly)
   decouples producers from consumers and makes the system resilient to bursts.

2. **Diagnose first, act second.** Knowing *why* a cart was abandoned before
   choosing a recovery action dramatically reduces wasted discounts. A payment
   failure needs a retry link, not a coupon.

3. **MCP makes AI agents composable.** Exposing business logic as MCP tools with
   typed schemas lets any AI model — Elastic Agent, Claude, GPT — call the same
   actions without custom integration code.

4. **Feedback loops are essential.** Publishing recovery events back into the
   same pipeline that ingests them ensures the system is self-correcting: carts
   get marked as recovered, analytics accumulate, and no cart is processed
   twice.

5. **Infrastructure-as-code pays off immediately.** A single CloudFormation
   template makes the entire stack reproducible across dev/staging/prod
   environments with one script. Changes to Lambda code, environment variables,
   or IAM policies are version-controlled alongside the application.

---

## Lessons Learnt

1. **Liquid templating inside Elasticsearch Workflows is powerful but
   unforgiving.** There is no syntax highlighting, no step-through debugger, and
   error messages are generic. Writing complex `if/elsif` chains with nested
   object access (`steps.fetch_latest_payment.output.hits.hits[0]._source.status`)
   requires extreme care with quoting and null checks.

2. **Test the decision matrix edge cases early.** The matrix has three
   dimensions (segment × reason × cart value) with fallback paths. Missing a
   combination leads to the global fallback ("reminder") — which looks correct
   in logs but masks the fact that a specific rule was never matched.

3. **EventBridge batching has sharp limits.** `PutEvents` accepts at most 10
   entries per call. The seed script batches accordingly, but production systems
   emitting hundreds of events per second need a queue or batching layer in
   front.

4. **SES sandbox mode blocks real email delivery.** During development every
   recipient email must be verified in SES. This was a recurring blocker when
   testing recovery emails against seed data with fake addresses. Moving to
   production SES requires an AWS support request.

5. **Cold-start chains amplify latency.** The MCP Server Lambda → Decision
   Engine Lambda → Recovery Action Lambda chain can hit 3 × cold-start latency
   (≈ 3–5 s total). Provisioned concurrency or keep-warm pings are worth
   considering for latency-sensitive deployments.

6. **Deterministic document IDs prevent data duplication but require
   coordination.** Using `state_{cart_id}` for cart_state upserts and
   `rec_{uuid}` for recovery_history means replayed events overwrite cleanly,
   but all Lambda functions must agree on the ID format.

7. **Separating "what to do" (Decision Engine) from "how to do it" (Recovery
   Action) into two Lambdas keeps each function small and independently
   testable**, but it means the AI Agent must correctly pass the output of one
   into the input of the other — a prompt-engineering challenge rather than a
   code challenge.

---

## How It Works

```
E-Commerce Events ──► EventBridge ──► Event Ingest Lambda ──► Elasticsearch
                                                                    │
                                           Scheduled Workflow (5 min) │
                                           detect_abandonment_reasons │
                                                                    │
                                                    ┌───────────────┘
                                                    ▼
                                          Elastic AI Agent
                                          (abandoned_cart)
                                                    │
                                    ┌───────────────┴───────────────┐
                                    ▼                               ▼
                          MCP: decision_engine           MCP: recovery_action
                          (S3 decision matrix)           (SES email + EventBridge)
                                                                    │
                                                    recovery_history │
                                                    event loops back ▼
                                                              EventBridge
```

### 1. Event Ingestion

All e-commerce events are emitted to **Amazon EventBridge**:

| Event type | Index |
|------------|-------|
| Customer profiles | `customer_profiles` |
| Cart activity (add to cart) | `cart_events` |
| Checkout progress/failures | `checkout_events` |
| Payment attempts | `payment_logs` |
| Page performance | `session_metrics` |
| Past recoveries | `recovery_history` |

An **Event Ingest Lambda** listens on EventBridge and indexes each event into
its Elasticsearch index. It also creates and maintains a `cart_state` document
per cart (`active` → `completed` → `recovery_sent`).

### 2. Scheduled Workflow

The `detect_abandonment_reasons` workflow runs **every 5 minutes** inside
Elasticsearch:

1. Query `cart_state` for carts where `status = active` and `check_at < now`
2. For each abandoned cart, fetch data from:
   `customer_profiles`, `cart_events`, `checkout_events`, `payment_logs`,
   `session_metrics`
3. Diagnose root cause using conditional branches:
   `payment_failure` → `pricing_shipping` → `performance_latency` →
   `browsing_or_window_shopping` → `unknown`
4. Emit a consolidated diagnosis payload with customer profile

### 3. Elastic AI Agent

The workflow calls an **Elastic AI Agent** (`abandoned_cart`) with the full
diagnosis. The agent executes two MCP tool calls in sequence.

### 4. MCP Tools

The agent connects to an **MCP Server** (API Gateway + Lambda) over Streamable
HTTP with API key auth:

| Tool | Lambda | Purpose |
|------|--------|---------|
| `decision_engine` | Reads decision matrix from S3 | Returns recommended action (payment_retry, discount, free_shipping, reminder, blocked) based on segment, reason, cart value, fraud risk |
| `recovery_action` | Sends email via SES | Delivers recovery message and publishes `recovery_history` event back to EventBridge (feedback loop) |

---

## Repository Structure

```
├── aws/
│   ├── stack.yml                          # CloudFormation (EventBridge, Lambdas, API GW, S3)
│   ├── deploy.sh                          # One-command deployment script
│   ├── DEPLOY.md                          # AWS deployment guide
│   ├── MCP_SERVER.md                      # MCP server architecture & usage
│   ├── decision-matrix/
│   │   └── decision-matrix.json           # Action rules by segment/reason/value
│   └── lambda/
│       ├── event_ingest/handler.py        # EventBridge → Elasticsearch indexer
│       ├── decision_engine/handler.py     # S3 matrix → recommended action
│       ├── mcp_server/handler.py          # JSON-RPC 2.0 MCP router
│       └── recovery_action/handler.py     # SES email + EventBridge history
├── elastic/
│   ├── mappings/                          # Index schemas (7 indices)
│   ├── queries/                           # Standalone query examples
│   ├── tools/                             # MCP tool + server definitions
│   └── workflows/
│       └── detect_abandonment_reasons.yml # Scheduled workflow (the core)
├── scripts/
│   ├── bootstrap_indices.py               # Create ES indices from mappings
│   └── seed_sample_data.py                # Send sample events to EventBridge
├── docs/
│   ├── architecture_diagram.md            # System architecture
│   ├── serverless_workflow_diagram.md     # Workflow step-by-step diagrams
│   ├── serverless_documentation.md        # Technical reference
│   ├── requirements_analysis.md           # Requirements compliance
│   └── sample_data_reference.md           # Test data reference
├── DEPLOYMENT.md                          # MCP server deployment summary
├── demo_script.md                         # 3-minute demo script
└── requirements.txt                       # Python dependencies
```

---

## Quickstart

### Prerequisites

- AWS account with permissions for Lambda, EventBridge, API Gateway, SES, S3
- Elasticsearch cluster (Elastic Cloud or self-hosted)
- Python 3.11+

### 1. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Elasticsearch
ES_ENDPOINT=https://your-cluster.es.us-east-1.aws.elastic-cloud.com
ES_API_KEY=your-es-api-key

# AWS
EVENT_BUS_NAME=ai-abandoned-cart-recovery-bus-dev
AWS_REGION=us-east-1
```

### 2. Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Deploy AWS Stack

```bash
cd aws && ./deploy.sh dev
```

This creates: EventBridge bus, Event Ingest Lambda, Decision Engine Lambda,
Recovery Action Lambda, MCP Server Lambda, API Gateway, S3 bucket with
decision matrix.

### 4. Bootstrap Elasticsearch

```bash
python scripts/bootstrap_indices.py
```

### 5. Seed Sample Data

```bash
python scripts/seed_sample_data.py
```

Events are sent to EventBridge → Lambda indexes them into Elasticsearch.

### 6. Import Workflow

1. Open Kibana → **Stack Management → Workflows**
2. Import `elastic/workflows/detect_abandonment_reasons.yml`
3. Enable the workflow

### 7. Create AI Agent

1. Go to **AI Assistants → Agent Builder**
2. Create agent with ID `abandoned_cart`
3. Add the MCP Server as a tool connector (see `aws/MCP_SERVER.md`)
4. The agent will be called automatically by the workflow

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture_diagram.md](docs/architecture_diagram.md) | System architecture (ASCII + Mermaid) |
| [docs/serverless_workflow_diagram.md](docs/serverless_workflow_diagram.md) | Workflow step-by-step with diagrams |
| [docs/serverless_documentation.md](docs/serverless_documentation.md) | Technical reference for all components |
| [docs/sample_data_reference.md](docs/sample_data_reference.md) | Test data and scenario reference |
| [docs/requirements_analysis.md](docs/requirements_analysis.md) | Requirements compliance analysis |
| [aws/MCP_SERVER.md](aws/MCP_SERVER.md) | MCP server architecture & usage |
| [aws/DEPLOY.md](aws/DEPLOY.md) | AWS deployment guide |
| [DEPLOYMENT.md](DEPLOYMENT.md) | MCP deployment summary |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

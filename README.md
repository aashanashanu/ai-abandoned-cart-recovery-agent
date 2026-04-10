# AI Abandoned Cart Recovery Agent

An event-driven system that detects abandoned shopping carts and triggers
personalised recovery actions using **AWS EventBridge + Lambda**,
**Elasticsearch**, an **Elastic AI Agent**, and two **MCP tools**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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

## Features

- **Event-driven ingestion** — EventBridge + Lambda pipeline indexes all events
  into Elasticsearch in real time
- **Automated detection** — Scheduled workflow finds abandoned carts every 5 min
- **Root-cause diagnosis** — Checks payment failures, shipping issues, latency,
  browsing patterns
- **AI-powered recovery** — Elastic AI Agent selects optimal action per customer
- **MCP integration** — Decision Engine and Recovery Action exposed as MCP tools
- **Feedback loop** — Recovery history loops back through EventBridge for tracking
- **Fraud guardrails** — High-risk customers get reminder-only or blocked actions

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

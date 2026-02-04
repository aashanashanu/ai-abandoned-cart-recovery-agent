# AI Abandoned Cart Recovery Agent for an E-commerce Platform

End-to-end hackathon project that demonstrates a **multi-step AI agent** (Elastic Agent Builder) that:

- Detects abandoned carts from event streams in **Elasticsearch**
- Diagnoses the likely root cause by correlating cart/checkout/payment/performance signals
- Finds similar historical cases and their recovery outcomes
- Chooses a best recovery action (discount, free shipping, reminder, payment retry)
- Triggers an automation hook (mock email/notification workflow)

## Architecture (high level)

- **Elasticsearch** stores behavioral + operational data:
  - `cart_events`, `checkout_events`, `payment_logs`, `session_metrics`, `recovery_history`, `customer_profiles`
- **Custom Tools Server** (FastAPI) exposes the agent’s tools over HTTP (and provides an OpenAPI spec).
- **Agent Orchestrator** (Python) demonstrates tool orchestration and multi-step flow.
- **Elastic Agent Builder** uses the tool server’s OpenAPI tool definitions and runs the agent as a multi-step workflow.

## Elasticsearch data model (indices)

- **`cart_events`** (`mappings/cart_events.json`)
  - Tracks add/remove/view cart events and cart value.
- **`checkout_events`** (`mappings/checkout_events.json`)
  - Tracks checkout progression (`step`, `status`), shipping costs, totals, payment method.
- **`payment_logs`** (`mappings/payment_logs.json`)
  - Tracks payment provider responses, failure codes, and retryability.
- **`session_metrics`** (`mappings/session_metrics.json`)
  - Tracks session performance signals (latency, error rate, apdex) to detect friction.
- **`recovery_history`** (`mappings/recovery_history.json`)
  - Stores recovery attempts, actions taken, and outcomes (used for similarity learning).
- **`customer_profiles`** (`mappings/customer_profiles.json`)
  - Stores customer contact info, segment, channel preference, and fraud risk.

## Custom agent tools (clear inputs/outputs)

All tools are exposed as HTTP endpoints in `src/tools_server/app.py` and automatically documented at:

- `http://localhost:8000/openapi.json`

Tool endpoints (operationIds match the names expected by Agent Builder):

- **`detect_abandoned_carts`** (`POST /tools/detect_abandoned_carts`)
  - Input: `lookback_minutes`, `abandonment_minutes`, `max_candidates`
  - Output: list of abandoned cart candidates (sorted by `cart_value`)
- **`analyze_abandonment`** (`POST /tools/analyze_abandonment`)
  - Input: `cart_id`
  - Output: diagnosis with `root_cause` + `signals` + evidence from correlated indices
- **`get_customer_profile`** (`POST /tools/get_customer_profile`)
  - Input: `customer_id`
  - Output: profile (segment + channel preference + fraud risk + contact fields)
- **`find_similar_abandonments`** (`POST /tools/find_similar_abandonments`)
  - Input: `{root_cause, segment, cart_value}`
  - Output: action success-rate stats + example historical documents
- **`decide_recovery_action`** (`POST /tools/decide_recovery_action`)
  - Input: cart + diagnosis + customer + similarity stats
  - Output: selected action + rationale
- **`trigger_recovery_action`** (`POST /tools/trigger_recovery_action`)
  - Input: cart + customer + action
  - Output: mock send result (`sent|skipped|failed`) + message_id
- **`record_recovery_attempt`** (`POST /tools/record_recovery_attempt`)
  - Input: cart + customer + diagnosis + action + sent_at
  - Output: `recovery_id` stored in `recovery_history`

## Repository structure

- `agent_builder/`
  - `agent.yaml` – agent definition (steps, tools, prompts) designed to be pasted/ported into Elastic Agent Builder
  - `elastic_agent_builder_setup.md` – UI setup guide for Kibana Agent Builder
- `mappings/` – index mappings (one file per index)
- `queries/` – example Elasticsearch DSL queries used by the agent
- `scripts/`
  - `bootstrap_indices.py` – creates indices with mappings
  - `seed_sample_data.py` – inserts small demo dataset
- `src/`
  - `es/client.py` – Elasticsearch client wrapper
  - `models/schemas.py` – request/response schemas
  - `tools_server/app.py` – custom tools API (OpenAPI)
  - `agent/orchestrator.py` – multi-step agent runner (detect→diagnose→similarity→decide→act)
  - `agent/policies.py` – recovery decision policy

## Quickstart

### 1) Start Elasticsearch (optional)

If you don’t already have an Elasticsearch cluster, use Docker:

```bash
docker compose up -d
```

### 2) Configure environment

Create a local `.env`:

```bash
cp .env.example .env
```

### 3) Install Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4) Bootstrap indices + seed data

```bash
python scripts/bootstrap_indices.py
python scripts/seed_sample_data.py
```

### 5) Start the custom tools server

```bash
uvicorn src.tools_server.app:app --reload --port 8000
```

OpenAPI spec:

- `http://localhost:8000/openapi.json`

### 6) Run the orchestrator (demo multi-step agent flow)

```bash
python -m src.agent.orchestrator
```

## How to use in Elastic Agent Builder

Follow `agent_builder/elastic_agent_builder_setup.md`.

At a high level:

- Create an agent in **Kibana → Elastic AI Assistant → Agent Builder** (or equivalent Agent Builder experience)
- Add tools from this server’s OpenAPI spec (`/openapi.json`)
- Paste/port the prompts and step descriptions from `agent_builder/agent.yaml`

## Hackathon requirements mapping

- **Custom multi-step AI agent using Elastic Agent Builder**
  - See: `agent_builder/agent.yaml` + `agent_builder/elastic_agent_builder_setup.md`
- **Agent must use custom tools**
  - Implemented as HTTP tools in: `src/tools_server/app.py` (OpenAPI at `/openapi.json`)
- **Agent must query and analyze data stored in Elasticsearch**
  - Index mappings in: `mappings/`
  - Sample DSL queries in: `queries/`
  - Executed by tool implementations in: `src/tools_server/app.py`
- **Automates a real business task (abandoned cart recovery)**
  - Automation hooks in: `src/tools_server/app.py` (mock email/notification) and `src/agent/orchestrator.py`

## Multi-step reasoning and tool orchestration (what to demo)

Two ways to demonstrate the workflow:

- **Elastic Agent Builder**
  - Step prompts and tool ordering are defined in `agent_builder/agent.yaml`.
- **Local orchestrator (reference implementation)**
  - `python -m src.agent.orchestrator` executes:
    - detect → analyze → profile → similarity → decide → trigger → record

## Business impact (what this enables)

- Reduces lost revenue by responding automatically to abandonment.
- Improves customer experience by diagnosing *why* checkout failed and choosing the least-intrusive recovery action.
- Learns from history by reusing patterns in `recovery_history` to pick higher-success actions.

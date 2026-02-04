# Elastic Agent Builder setup (hackathon-ready)

This project ships a **custom tools server** that exposes the agent’s tools via an **OpenAPI spec**.

## Prerequisites

- Kibana + Elasticsearch running (see `docker-compose.yml`)
- Tools server running:

```bash
uvicorn src.tools_server.app:app --reload --port 8000
```

OpenAPI:

- `http://localhost:8000/openapi.json`

## Steps in Agent Builder

1. In Kibana, open the Agent Builder experience for Elastic AI Assistant.
2. Create a new agent:
   - Name: `Abandoned Cart Recovery Agent`
   - Goal: Recover abandoned carts by diagnosing root cause and triggering the best action.
3. Add tools from OpenAPI:
   - Add a tool set from URL: `http://localhost:8000/openapi.json`
   - Confirm the following tools appear:
     - `detect_abandoned_carts`
     - `analyze_abandonment`
     - `get_customer_profile`
     - `find_similar_abandonments`
     - `decide_recovery_action`
     - `trigger_recovery_action`
     - `record_recovery_attempt`
4. Configure the agent’s multi-step workflow:
   - Copy the step structure/prompts from `agent_builder/agent.yaml`
   - Ensure the agent is allowed to call tools
5. Test with a “run now” instruction:

```text
Detect abandoned carts in the last 24h using a 30 minute abandonment window, diagnose the top 3, and trigger the best recovery action.
```

## Expected behavior

The agent should:

- Call `detect_abandoned_carts`
- For each cart, call `analyze_abandonment` + `get_customer_profile`
- Call `find_similar_abandonments`
- Call `decide_recovery_action`
- Call `trigger_recovery_action`
- Call `record_recovery_attempt`

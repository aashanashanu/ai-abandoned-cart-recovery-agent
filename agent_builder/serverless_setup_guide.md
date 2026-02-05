# Elastic Agent Builder Setup Guide

## Overview

This guide helps you set up the AI Abandoned Cart Recovery Agent using Elastic Serverless workflows.

## Prerequisites

- Elastic Serverless project with Kibana access
- API key with permissions for indices and workflows
- Python environment for data setup

## Step 1: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your Serverless details:
```env
ES_SERVERLESS_ENDPOINT=https://your-project-id.es.us-east-1.aws.elastic-cloud.com
ES_SERVERLESS_API_KEY=your-api-key
```

## Step 2: Bootstrap Elasticsearch

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create indices and seed data
python scripts/bootstrap_indices.py
python scripts/seed_sample_data.py
```

## Step 3: Import Workflow

1. Open your Serverless Kibana
2. Navigate to **Stack Management → Workflows**
3. Click **Create workflow** or **Import**
4. Import `elastic_workflows/serverless_workflow.yml`
5. **Save** and **Enable** the workflow

## Step 4: Create Agent

1. Go to **AI Assistants → Agent Builder**
2. Click **Create agent**
3. Import or paste contents of `agent_builder/serverless_agent.yaml`
4. Configure:
   - Model: `gpt-4o-mini`
   - Temperature: `0.1`
   - Max tokens: `1024`
5. **Save** the agent

## Step 5: Test the Agent

Use this test prompt:
```

## Expected behavior

The agent should:
- Call `detect_abandoned_carts` to find candidates
- For each cart, call `analyze_abandonment` to diagnose the root cause
- Enrich with `get_customer_profile`
- Find similar cases with `find_similar_abandonments`
- Decide an action with `decide_recovery_action`
- Trigger with `trigger_recovery_action`
- Record the attempt with `record_recovery_attempt`

## Troubleshooting

- If tools fail to load, verify the tools server is running and accessible from Kibana
- If Elasticsearch queries fail, ensure your Serverless API key has the necessary permissions
- If the agent stalls, check the Agent Builder’s execution trace for tool call errors

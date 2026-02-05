# Project Documentation

## Overview

The AI Abandoned Cart Recovery Agent is a serverless solution that automatically detects abandoned shopping carts, diagnoses abandonment causes, and triggers personalized recovery actions using Elastic Serverless and AI.

## Architecture Components

### 1. Elasticsearch Indices

#### Mappings (`/mappings/`)
Define schema for each index:

- **cart_events**: Tracks cart activity (add, remove, view events)
  - Fields: cart_id, customer_id, session_id, event_type, product_id, quantity, unit_price, cart_value, currency, device_type, page, referrer, @timestamp
  
- **checkout_events**: Records checkout process steps
  - Fields: checkout_id, cart_id, customer_id, session_id, step, status, shipping_method, payment_method, shipping_cost, tax, total, currency, @timestamp
  
- **customer_profiles**: Customer segmentation and preferences
  - Fields: customer_id, email, segment, fraud_risk, preferred_channel, created_at, last_order_at, total_orders, total_spent, @timestamp
  
- **payment_logs**: Payment attempts and failures
  - Fields: payment_id, checkout_id, cart_id, customer_id, provider, status, failure_code, failure_message, retryable, gateway_latency_ms, attempt, @timestamp
  
- **recovery_history**: Recovery actions and outcomes
  - Fields: recovery_id, cart_id, customer_id, segment, cart_value, currency, diagnosis (root_cause, signals), action (type, channel, discount_percent, free_shipping, template), outcome (status, order_id, revenue_recovered, outcome_at), @timestamp
  
- **session_metrics**: Performance data
  - Fields: session_id, customer_id, page_load_time, api_latency_ms, error_count, device_type, browser, @timestamp

### 2. Elasticsearch Queries

**Note:** All queries are now embedded directly in the workflow file (`/elastic_workflows/serverless_workflow.yml`) for self-contained deployment.

Previously, queries were structured as separate JSON files:
- `detect_abandoned_carts.json` - Finds carts idle 30+ minutes
- `analyze_abandonment_cart_checkout.json` - Gets checkout events for analysis
- `analyze_abandonment_payment_logs.json` - Identifies payment issues
- `find_similar_abandonments.json` - Searches historical cases

**Current Implementation:**
All Elasticsearch queries are now embedded inline within the workflow steps:
- **detect_carts** step queries `cart_events` index
- **analyze_abandonment** step queries `checkout_events` index  
- **get_customer** step queries `customer_profiles` index
- **record_attempt** step indexes to `recovery_history`

### 3. Scripts

#### Bootstrap (`/scripts/bootstrap_indices.py`)
Creates Elasticsearch indices with proper schema:

```python
# Key features:
- Prioritizes Serverless connection
- Removes unsupported settings for Serverless
- Creates indices from mapping files
- Handles existing indices gracefully
```

#### Data Seeding (`/scripts/seed_sample_data.py`)
Populates indices with sample data:

```python
# Generates:
- Customer profiles with varying segments
- Cart events with abandonment patterns
- Checkout events with different failure points
- Payment logs with retry scenarios
- Session metrics with performance data
- Recovery history with outcomes
```

### 4. Serverless Workflow (`/elastic_workflows/serverless_workflow.yml`)

Single workflow file that executes:

1. **detect_carts**: Query cart_events for abandoned carts
2. **analyze_abandonment**: Correlate with checkout_events
3. **get_customer**: Fetch customer profile
4. **decide_action**: AI chooses recovery strategy
5. **trigger_action**: Send recovery via HTTP
6. **record_attempt**: Store in recovery_history

### 5. Agent Definition (`/agent_builder/serverless_agent.yaml`)

Configures AI agent with:
- Model settings (gpt-4o-mini, temp 0.1)
- Guardrails for business rules
- Reference to serverless workflow

## Data Flow

```
Cart Events ──┐
               ├──► Detect Abandonment
Checkout Events ─┤
               ├──► Analyze Signals
Customer Data ──┤
               ├──► Decide Action
Payment Logs ────┤
               ├──► Trigger Recovery
History Data ────┘
               └──► Record Attempt
```

## Key Features

### Serverless-First Design
- No infrastructure to manage
- Automatic scaling
- Built-in security
- Pay-per-use pricing

### Schema Enforcement
- Strict dynamic mapping
- Type validation
- Field constraints
- Index templates

### Query Optimization
- Pre-built aggregations
- Efficient filters
- Sorted results
- Size limits

### Guardrails
- No discounts for high fraud risk
- Prefer payment_retry for failures
- Use reminder for performance issues

## Deployment

### Prerequisites
- Elastic Serverless project
- API key with proper permissions
- Python environment

### Steps
1. Configure environment (.env)
2. Bootstrap indices
3. Seed sample data
4. Import workflow to Kibana
5. Create agent in Agent Builder
6. Test with sample prompt

## Monitoring

Track recovery performance in Kibana:
- Recovery rate by action type
- Conversion by customer segment
- Revenue recovered per campaign

## Troubleshooting

Common issues and solutions:

### Workflow Import Errors
- Check `data.set` type usage
- Verify `connector-id` values
- Validate Liquid syntax

### Query Failures
- Confirm index names match
- Check field mappings
- Verify API permissions

### No Results
- Run seed script
- Check time ranges
- Validate data format

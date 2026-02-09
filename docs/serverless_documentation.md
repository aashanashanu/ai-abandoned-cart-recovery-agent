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

Single workflow file that executes a comprehensive abandoned cart recovery process:

#### Main Steps:
1. **detect_abandoned_carts**: Query cart_events for carts from last 24 hours with add_to_cart events but no checkout completion
2. **analyze_abandonment_reasons**: For each abandoned cart, execute nested analysis:
   - **check_checkout_attempts**: Query checkout_events for the cart
   - **conditionalStep**: If checkout attempts exist and weren't completed:
     - **check_payment_logs**: Query payment_logs for payment failures
     - **add_abandonment_reason**: Determine root cause (payment_failure, shipping_issue, browsing_abandonment)
     - **fetch_customer_profile**: Get customer segmentation data
     - **set_customer_data**: Consolidate all customer and cart information
     - **set_recovery_action**: Complex decision logic for action selection
     - **send_notification**: Prepare HTTP request data
     - **record_recovery_attempt**: Index recovery attempt to recovery_history

#### Decision Logic:
The workflow uses sophisticated conditional logic based on:
- **Customer Segment**: VIP, Standard
- **Fraud Risk**: High, Normal
- **Cart Value**: >$500 (VIP), >$300 (Standard)
- **Abandonment Reason**: payment_failure, shipping_issue, browsing_abandonment

#### Action Types:
- **payment_retry**: For payment failures (VIP/Standard segments)
- **discount**: 15% for VIP >$500, 10% for Standard >$300
- **free_shipping**: For shipping issues or VIP customers
- **reminder**: Default action for browsing abandonment
- **blocked**: No action for high fraud risk with payment failure
- **reminder_only**: For high fraud risk customers

### 5. Agent Definition (`/agent_builder/serverless_agent.yaml`)

Configures AI agent with:
- Model settings (gpt-4o-mini, temp 0.1)
- Guardrails for business rules
- Reference to serverless workflow

## Data Flow

```
Cart Events ──┐
               ├──► Detect Abandonment (24h window)
Checkout Events ─┤
               ├──► For Each Cart: Analyze abandonment reason
Customer Data ──┤
               ├──► Check checkout attempts → payment logs
Payment Logs ────┤
               ├──► Determine root cause (payment/shipment/browsing)
History Data ────┘
               ├──► Fetch customer profile & segment
               ├──► Apply complex decision logic
               ├──► Prepare notification data
               └──► Record recovery attempt
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
- No discounts for high fraud risk customers
- Block actions for high fraud risk + payment failure
- Prefer payment_retry for payment failures
- Use reminder_only for high fraud risk customers
- VIP customers get preferential treatment (free shipping, higher discounts)
- Cart value thresholds trigger different actions

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

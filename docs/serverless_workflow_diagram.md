# Workflow Flow Diagram

## Mermaid Diagram

```mermaid
flowchart TD
    A[Manual Trigger] --> B[detect_carts]
    B --> C[set_cart_id]
    C --> D[analyze_abandonment]
    D --> E[set_customer_id]
    E --> F[get_customer]
    F --> G[set_email]
    G --> H[decide_action]
    H --> I[set_action]
    I --> J[trigger_action]
    J --> K[set_timestamp]
    K --> L[record_attempt]
    
    B --> |Query cart_events<br/>Find abandoned carts| B1[ES Query]
    D --> |Query checkout_events<br/>Get checkout data| D1[ES Query]
    F --> |Query customer_profiles<br/>Get customer info| F1[ES Query]
    G --> |AI inference<br/>Choose recovery action| H1[ML Model]
    J --> |HTTP POST<br/>Send recovery| J1[External API]
    K --> |Index recovery_history<br/>Store attempt| L1[ES Index]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style D fill:#fff3e0
    style F fill:#ffebee
    style G fill:#e8f5e8
    style H fill:#ff9800
    style I fill:#ffeb3b
    style J fill:#ffebee
    style K fill:#e8f5e8
    style L fill:#e8f5e8
```

## ASCII Diagram

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Cart Events   │    │  Checkout Events │    │ Customer Profile│
│   (ES Index)    │    │   (ES Index)    │    │   (ES Index)    │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         │                      │                        │
         └──────────────────────┼────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Serverless Workflow  │
                    │                      │
                    │ 1. Detect Carts      │
                    │ 2. Analyze Signals   │
                    │ 3. Get Customer     │
                    │ 4. Decide Action     │
                    │ 5. Trigger Recovery  │
                    │ 6. Record Attempt    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Recovery Actions     │
                    │  - Payment Retry     │
                    │  - Discount          │
                    │  - Free Shipping     │
                    │  - Reminder          │
                    └──────────────────────┘
```

## Step Details

| Step | Type | Connector | Purpose |
|------|------|-----------|---------|
| detect_carts | data.set | elasticsearch-query | Find carts abandoned 30+ minutes |
| set_cart_id | data.set | - | Extract cart ID for next steps |
| analyze_abandonment | data.set | elasticsearch-query | Get checkout events for cart |
| set_customer_id | data.set | - | Extract customer ID |
| get_customer | data.set | elasticsearch-query | Fetch customer profile |
| set_email | data.set | - | Extract customer email |
| decide_action | inference.completion_stream | ml | AI chooses recovery action |
| set_action | data.set | - | Store chosen action |
| trigger_action | data.set | http | Send recovery via API |
| set_timestamp | data.set | - | Capture current time |
| record_attempt | data.set | elasticsearch-index | Store for learning |

## Key Variables

- `{{detect_carts.output.aggregations.carts.buckets.0.key}}` - Cart ID
- `{{analyze_abandonment.output.hits.hits.0._source.customer_id}}` - Customer ID
- `{{get_customer.output.hits.hits.0._source.email}}` - Customer email
- `{{decide_action.output}}` - Chosen recovery action
- `{{$now}}` - Current timestamp

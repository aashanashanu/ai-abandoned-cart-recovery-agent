# Serverless Workflow Diagram

## 🔄 Complete Abandoned Cart Recovery Workflow

```mermaid
flowchart TD
    A[Start] --> B[Detect Carts]
    B --> C[Analyze Abandonment]
    C --> D[Get Customer Profile]
    D --> E[Decide Action]
    E --> F[Trigger Recovery Action]
    F --> G[Record Attempt]
    G --> H[End]

    subgraph "Decision Logic"
        direction LR
        E --| "VIP + Payment Failure" -->| "Payment Retry"
        E --| "VIP + High Value (>500)" -->| "Discount"
        E --| "VIP + Other Issues" -->| "Free Shipping"
        E --| "High Fraud Risk + Payment Failure" -->| "Blocked"
        E --| "High Fraud Risk + Other" -->| "Reminder Only"
        E --| "Standard + Payment Failure" -->| "Payment Retry"
        E --| "Standard + High Value (>300)" -->| "Discount"
        E --| "Standard + Shipping Issues" -->| "Free Shipping"
        E --| "Standard + Other Issues" -->| "Reminder"
        E --| "Default Cases" -->| "Reminder"

    classDef fill:#f9f9f9,stroke:#333,color:#333
    classDef fill:#e1f5e3,stroke:#333,color:#333

    classDef fill:#ffeb3b,stroke:#333,color:#333
```

## 📋 Workflow Steps

### A. Detect Carts
**Purpose**: Find abandoned carts from last 24 hours
**Input**: Time range, cart events
**Output**: List of abandoned cart IDs
**Key Fields**: `@timestamp`, `event_type`, `cart_id`

### B. Analyze Abandonment
**Purpose**: Diagnose abandonment reasons for each cart
**Input**: Cart ID, checkout events
**Output**: Root cause analysis
**Key Fields**: `step`, `status`, `issues`

### C. Get Customer Profile
**Purpose**: Retrieve customer segmentation data
**Input**: Customer ID from analysis
**Output**: Customer profile with segment and risk level
**Key Fields**: `segment`, `fraud_risk`, `lifetime_value`

### D. Decide Action
**Purpose**: Intelligent action selection based on context
**Input**: Customer profile, abandonment analysis, cart data
**Output**: Recovery action type
**Decision Factors**:
- Customer segment (VIP, Standard, High Fraud Risk)
- Abandonment cause (Payment Failure, Shipping Issues, Performance)
- Cart value and items

### E. Trigger Recovery Action
**Purpose**: Execute recovery action via external API
**Input**: Action type, customer contact, cart details
**Output**: HTTP request to recovery service
**Key Fields**: `action.type`, `channel`, `to`, `cart_id`

### F. Record Attempt
**Purpose**: Log recovery attempt for analytics and learning
**Input**: Action details, outcome
**Output**: Recovery history document
**Key Fields**: `action`, `outcome`, `revenue_recovered`, `sent_at`

---

## 🎯 Decision Logic Matrix

### Customer Segments

| Segment | Payment Failure | Shipping Issues | High Value | Default |
|----------|-----------------|-----------------|------------|-----------|
| **VIP** | Payment Retry | Free Shipping | Discount | Free Shipping |
| **High Fraud Risk** | Blocked | Reminder | Reminder | Reminder |
| **Standard** | Payment Retry | Free Shipping | Discount | Reminder |

### Action Types

- **payment_retry**: Alternative payment method attempt
- **free_shipping**: Remove shipping cost barrier
- **reminder**: Gentle reminder notification
- **discount**: Percentage discount offer
- **blocked**: No action due to fraud risk

### Success Indicators

- **High Success**: VIP + Payment Retry (85%)
- **Medium Success**: Standard + Free Shipping (65%)
- **Low Success**: Standard + Reminder (40%)
- **Blocked**: High Fraud Risk + Reminder (25%)

---

## 🔧 Technical Implementation

### Elasticsearch Queries

```json
{
  "detect_carts": {
    "index": "cart_events",
    "query": {
      "bool": {
        "must": [
          {"range": {"@timestamp": {"gte": "now-1440m"}}},
          {"term": {"event_type": "add"}}
        ],
        "must_not": [
          {"exists": {"field": "checkout_completed"}}
        ]
      }
    },
    "aggs": {
      "carts": {
        "terms": {"field": "cart_id", "size": 20}
      }
    }
  }
}
```

### Data Flow

```
Cart Events → Abandonment Detection → Customer Profile Lookup → Action Decision → Recovery Execution → History Recording
      ↓                    ↓                    ↓              ↓
   Time-based           Segment-based          Context-aware      API-based        Analytics
   Aggregation           Profile retrieval        Rule-based        HTTP POST       Index update
```

### Serverless Benefits

- **🚀 Scalability**: No infrastructure management
- **💰 Cost-effective**: Pay-per-execution model
- **🔒 Security**: Built-in authentication and authorization
- **📊 Monitoring**: Complete audit trail in recovery_history
- **🎯 Intelligence**: Context-aware decision making
- **⚡ Performance**: Sub-second execution times

---

## 🎪 Integration Points

### Agent Builder Integration
- **Workflow Tool**: Uses `elastic-workflows/serverless_workflow.yml`
- **AI Model**: GPT-4o-mini for decision support
- **Guardrails**: Business rules embedded in workflow logic
- **Chat Interface**: Natural language commands and responses

### External Systems
- **Recovery Service**: HTTP endpoint for email/SMS/push
- **Analytics**: Kibana dashboards for performance monitoring
- **Learning**: Recovery history analysis for strategy optimization

This workflow demonstrates a complete, production-ready abandoned cart recovery system using Elastic Serverless and AI Agent Builder.

## Decision Matrix

This document presents the decision matrix used by the **Decision Engine** Lambda (`decision_engine` MCP tool).  
Source file: [`aws/decision-matrix/decision-matrix.json`](../aws/decision-matrix/decision-matrix.json)

### Legend

| Column | Description |
|---|---|
| **Segment** | Customer segment — `VIP`, `standard`, `high_fraud_risk`, `default` |
| **Root Cause** | Diagnosis from the Elastic workflow — `payment_failure`, `high_cart_value`, `shipping_issue`, `browsing_abandonment` |
| **Action Type** | Recovery action — `payment_retry`, `discount`, `free_shipping`, `reminder`, `reminder_only`, `blocked` |
| **Discount** | Percentage discount offered (if any) |
| **Free Shipping** | Whether free shipping is included |
| **Cart Value Threshold** | Minimum cart value required for the action to apply |

---

### Recovery Actions by Segment

| Segment | Root Cause | Action Type | Discount | Free Shipping | Cart Value Threshold | Message |
|---|---|---|:---:|:---:|:---:|---|
| **VIP** | `payment_failure` | `payment_retry` | — | No | — | We noticed an issue with your payment. Try an alternative payment method. |
| **VIP** | `high_cart_value` | `discount` | 15% | No | $500 | Complete your purchase and enjoy 15% off! |
| **VIP** | `shipping_issue` | `free_shipping` | — | Yes | — | Great news! We're offering free shipping on your order. |
| **VIP** | `browsing_abandonment` | `free_shipping` | — | Yes | — | As a VIP, enjoy free shipping on your cart items! |
| **high_fraud_risk** | `payment_failure` | `blocked` | — | No | — | Your order is under review. No action taken. |
| **high_fraud_risk** | `shipping_issue` | `reminder_only` | — | No | — | You left items in your cart. Complete your purchase when ready. |
| **high_fraud_risk** | `browsing_abandonment` | `reminder_only` | — | No | — | You left items in your cart. Complete your purchase when ready. |
| **standard** | `payment_failure` | `payment_retry` | — | No | — | Your payment didn't go through. Try an alternative payment method. |
| **standard** | `high_cart_value` | `discount` | 10% | No | $300 | Complete your purchase and get 10% off! |
| **standard** | `shipping_issue` | `free_shipping` | — | Yes | — | We're offering free shipping to help complete your order! |
| **standard** | `browsing_abandonment` | `reminder` | — | No | — | You left items in your cart. Don't miss out! |
| **default** | `payment_failure` | `payment_retry` | — | No | — | Your payment didn't go through. Please try again. |
| **default** | `shipping_issue` | `reminder` | — | No | — | Complete your purchase today. |
| **default** | `browsing_abandonment` | `reminder` | — | No | — | Complete your purchase today. |

---

### Segment Comparison

| Feature | VIP | Standard | High Fraud Risk | Default |
|---|:---:|:---:|:---:|:---:|
| Payment failure action | Retry | Retry | **Blocked** | Retry |
| High-value cart discount | 15% (≥ $500) | 10% (≥ $300) | — | — |
| Shipping incentive | Free shipping | Free shipping | Reminder only | Reminder |
| Browsing abandonment | Free shipping | Reminder | Reminder only | Reminder |

---

### Success Indicators

| Action Type | Best Segment | Estimated Success Rate |
|---|---|:---:|
| `payment_retry` | VIP | **85%** |
| `free_shipping` | standard | **65%** |
| `reminder` | standard | **40%** |
| `blocked` | high_fraud_risk | **0%** |

---

### Notes

- The decision matrix lives in S3 at `s3://<bucket>/decision-matrix/decision-matrix.json`. The `decision_engine` Lambda loads and caches this file in memory on cold start.
- To change recovery business rules, update the JSON file — no code changes or redeployment required.
- `high_fraud_risk` customers are **never** offered discounts or free shipping — only reminders or blocks.

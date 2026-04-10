## Decision Matrix

This document presents the decision matrix used by the `decision_engine` tool. It lists recommended recovery actions per customer segment and root cause, plus incentives and thresholds.

### Legend
- **Segment**: customer segment (VIP, standard, high_fraud_risk, default)
- **Root cause**: diagnosis from workflow (payment_failure, high_cart_value, shipping_issue, browsing_abandonment)
- **Action Type**: recovery action type (payment_retry, discount, free_shipping, reminder, blocked, reminder_only)
- **Discount**: percent discount to offer (if any)
- **Free Shipping**: whether to offer free shipping
- **Cart Value Threshold**: minimum cart value for the action to apply (when present)

### Matrix

| Segment | Root Cause | Action Type | Message | Discount | Free Shipping | Cart Value Threshold |
|---|---|---|---|---:|:---:|---:|
| VIP | payment_failure | payment_retry | We noticed an issue with your payment. Try an alternative payment method. | — | No | — |
| VIP | high_cart_value | discount | Complete your purchase and enjoy 15% off! | 15% | No | 500 |
| VIP | shipping_issue | free_shipping | Great news! We're offering free shipping on your order. | — | Yes | — |
| VIP | browsing_abandonment | free_shipping | As a VIP, enjoy free shipping on your cart items! | — | Yes | — |

| high_fraud_risk | payment_failure | blocked | Your order is under review. No action taken. | — | No | — |
| high_fraud_risk | shipping_issue | reminder_only | You left items in your cart. Complete your purchase when ready. | — | No | — |
| high_fraud_risk | browsing_abandonment | reminder_only | You left items in your cart. Complete your purchase when ready. | — | No | — |

| standard | payment_failure | payment_retry | Your payment didn't go through. Try an alternative payment method. | — | No | — |
| standard | high_cart_value | discount | Complete your purchase and get 10% off! | 10% | No | 300 |
| standard | shipping_issue | free_shipping | We're offering free shipping to help complete your order! | — | Yes | — |
| standard | browsing_abandonment | reminder | You left items in your cart. Don't miss out! | — | No | — |

| default | payment_failure | payment_retry | Your payment didn't go through. Please try again. | — | No | — |
| default | shipping_issue | reminder | Complete your purchase today. | — | No | — |
| default | browsing_abandonment | reminder | Complete your purchase today. | — | No | — |

---

### Success Indicators

| Action Type | Target Segment | Estimated Success Rate |
|---|---|---:|
| payment_retry | VIP | 85% |
| free_shipping | standard | 65% |
| reminder | standard | 40% |
| blocked | high_fraud_risk | 0% |

---

Notes:
- Keep the decision matrix in `aws/decision-matrix/decision-matrix.json`. The `decision_engine` Lambda loads and caches this file at runtime.
- Update the JSON to change business rules without changing code.

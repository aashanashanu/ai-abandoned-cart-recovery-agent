# Demo Walkthrough Script: AI Abandoned Cart Recovery Agent

## Demo Overview (3 minutes)

**Goal:** Show how Elastic Serverless + AI automatically recovers abandoned carts with personalized actions.

**Key Points:**
- All queries embedded in single workflow file
- No external tools server needed
- AI diagnoses abandonment cause and chooses optimal recovery
- Built-in guardrails prevent inappropriate actions

---

## Script Flow

### Opening (0:00–0:30)

"Every e-commerce site loses revenue when shoppers abandon carts. Generic 'discount blasts' waste margin and miss the real issue. Our AI agent diagnoses why carts are abandoned and triggers the best recovery action—automatically."

**Show:**
- Repository structure with serverless workflow
- Single `serverless_workflow.yml` file with embedded queries
- No external dependencies

### Demo Scenario 1: Payment Failure (0:30–1:00)

**Expected Behavior:** Alex (VIP customer) abandoned cart after payment declined

**What happens:**
1. Agent detects cart abandoned 30+ minutes
2. Finds payment failure in checkout events
3. Retrieves Alex's VIP profile
4. AI diagnoses: "payment_failure - card_declined"
5. Chooses: "payment_retry" (no discount for VIP)
6. Sends email: "Your card was declined, try again?"

**Show in Kibana:**
- Cart events for cart_1001
- Payment failure logs
- Customer profile (VIP, low fraud risk)
- Recovery action triggered

### Demo Scenario 2: High Shipping Cost (1:00–1:30)

**Expected Behavior:** Jamie (standard customer) stalled at shipping step

**What happens:**
1. Agent detects cart abandoned during checkout
2. Finds shipping step abandonment
3. Retrieves Jamie's standard profile
4. AI diagnoses: "pricing_shipping - high_shipping_cost"
5. Chooses: "free_shipping" (cost-effective for standard segment)
6. Sends push notification: "Free shipping on your order!"

**Show in Kibana:**
- Checkout events showing shipping step
- Session metrics (good performance)
- Recovery action with free shipping

### Demo Scenario 3: Performance Issues (1:30–2:00)

**Expected Behavior:** Taylor (new customer) experienced slow checkout

**What happens:**
1. Agent detects cart abandonment
2. Finds no checkout attempts
3. Retrieves Taylor's new customer profile
4. AI diagnoses: "performance_latency - high_latency"
5. Chooses: "reminder" (no discount for performance issues)
6. Sends email: "Having trouble? Your cart is waiting"

**Show in Kibana:**
- Cart events only (no checkout)
- Session metrics showing high latency
- Reminder action triggered

### Demo Scenario 4: High Fraud Risk (2:00–2:15)

**Expected Behavior:** Sam (high fraud risk) abandoned expensive cart

**What happens:**
1. Agent detects cart abandonment
2. Finds payment failure
3. Retrieves Sam's high fraud risk profile
4. AI diagnoses: "payment_failure - card_declined"
5. **Guardrail applies:** No discounts for high fraud risk
6. Chooses: "reminder" (not discount)
7. Sends email: "Your cart is saved for later"

**Show in Kibana:**
- Customer profile showing high fraud risk
- Guardrail preventing discount
- Reminder action instead

### Demo Scenario 5: Learning from History (2:15–2:30)

**Expected Behavior:** Agent learns from past recoveries

**What happens:**
1. Agent finds similar abandonment patterns
2. Checks recovery history for this segment
3. Sees 80% success with free shipping for standard customers
4. Chooses proven successful action

**Show in Kibana:**
- Recovery history dashboard
- Success rates by action type
- AI choosing based on historical success

### Closing (2:30–3:00)

"With Elastic Serverless workflows and AI, you turn abandoned carts into recovered revenue—safely, automatically, and at scale. Everything runs in a single workflow file with embedded queries, no external servers needed."

---

## Expected Test Results

### Scenario 1: Payment Failure (VIP)
- **Cart ID:** cart_1001
- **Customer:** alex@example.com (VIP)
- **Diagnosis:** payment_failure
- **Action:** payment_retry
- **Channel:** email
- **Discount:** 0%
- **Expected:** High recovery rate

### Scenario 2: High Shipping Cost (Standard)
- **Cart ID:** cart_2002
- **Customer:** jamie@example.com (Standard)
- **Diagnosis:** pricing_shipping
- **Action:** free_shipping
- **Channel:** push
- **Discount:** 0%
- **Expected:** Medium recovery rate

### Scenario 3: Performance Issues (New)
- **Cart ID:** cart_3003
- **Customer:** taylor@example.com (New)
- **Diagnosis:** performance_latency
- **Action:** reminder
- **Channel:** email
- **Discount:** 0%
- **Expected:** Low-medium recovery rate

### Scenario 4: High Fraud Risk
- **Cart ID:** cart_4004
- **Customer:** sam@example.com (High Risk)
- **Diagnosis:** payment_failure
- **Action:** reminder (guardrail)
- **Channel:** email
- **Discount:** 0%
- **Expected:** Low recovery rate (safety first)

### Scenario 5: Learning from History
- **Cart ID:** cart_5005
- **Customer:** maria@example.com (International)
- **Diagnosis:** checkout_friction
- **Action:** Based on segment history
- **Channel:** email
- **Discount:** Varies by success rate
- **Expected:** Adaptive recovery rate

---

## Test Prompts

### Basic Test
```
Detect abandoned carts in the last 24h, diagnose the top 3, and trigger the best recovery action.
```

### Scenario-Specific Tests
```
Recover cart_1001 for customer cust_001 - check for payment failures and choose appropriate action.
```

```
Analyze cart_2002 abandonment pattern and recommend recovery for standard segment customer.
```

```
Handle cart_4004 with high fraud risk - apply appropriate guardrails and safe recovery action.
```

### Learning Test
```
Review recovery history for standard segment customers and apply learnings to new abandonment case.
```

---

## Tips for Delivery

- Show the workflow diagram (`docs/serverless_workflow_diagram.md`) when explaining steps
- If demoing live, import `elastic_workflows/serverless_workflow.yml` into Kibana Workflows
- Highlight that everything runs serverless—no external tools server needed
- Emphasize the single workflow file approach with embedded queries
- Point out guardrails in action for high fraud risk scenario
- Show how AI learns from recovery history

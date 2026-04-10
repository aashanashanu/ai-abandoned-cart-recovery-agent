# Deploy – AI Abandoned Cart Recovery Agent (AWS)

This file documents how to deploy the unified AWS stack which includes:

1. **Event Ingest** – EventBridge → Lambda pipeline that indexes events into Elasticsearch and maintains `cart_state` documents.
2. **Decision Engine** – Lambda that reads a decision matrix from S3 and determines recovery actions.

## Files

| File | Purpose |
|------|---------|
| `aws/stack.yml` | Merged CloudFormation / SAM template |
| `aws/lambda/event_ingest/handler.py` | Event ingest Lambda |
| `aws/lambda/decision_engine/handler.py` | Decision engine Lambda |
| `aws/decision-matrix/decision-matrix.json` | Decision matrix (uploaded to S3) |
| `aws/deploy.sh` | One-command deploy script |

## Quick Deploy

```bash
# From the repo root
./aws/deploy.sh dev
```

## Step-by-Step

1. Install Python dependencies for local testing:
```bash
pip install -r requirements.txt
```

2. Build & deploy with SAM:
```bash
sam build
sam deploy --template-file aws/stack.yml \
  --stack-name ai-abandoned-cart-recovery-dev \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    Environment=dev \
    EsEndpoint=https://search-your-es.example.com \
    CheckAtMinutes=30 \
    EventBusName=abandoned-cart-recovery-bus
```

3. Or deploy with the AWS CLI:
```bash
aws cloudformation deploy \
  --template-file aws/stack.yml \
  --stack-name ai-abandoned-cart-recovery-dev \
  --parameter-overrides Environment=dev ProjectName=ai-abandoned-cart-recovery \
  --capabilities CAPABILITY_NAMED_IAM
```

4. Post-deploy:
- Confirm the Event Ingest Lambda environment variables include `ES_ENDPOINT` and the chosen authentication method (`ES_API_KEY` or `ES_USERNAME`/`ES_PASSWORD`).
- Confirm `CHECK_AT_MINUTES` is set to the desired value.
- The deploy script automatically uploads the decision matrix to S3 and updates the Decision Engine Lambda code.

5. Sending seed events:
```bash
export AWS_PROFILE=your-profile
export EVENT_BUS_NAME=abandoned-cart-recovery-bus
python scripts/seed_sample_data.py
```

## Notes
- `ES_ENDPOINT` – Elasticsearch/OpenSearch endpoint. Use `ES_API_KEY` (recommended) or `ES_USERNAME`/`ES_PASSWORD` for auth.
- `CHECK_AT_MINUTES` – controls how far ahead `check_at` is set for `cart_state` documents.
- `DECISION_BUCKET` – automatically set from the stack output; the Lambda reads `decision-matrix.json` from this bucket.

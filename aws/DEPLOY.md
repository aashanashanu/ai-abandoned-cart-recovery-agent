# Deploy EventBridge → Lambda (Event ingestion)

This file documents how to deploy the EventBridge → Lambda ingestion pipeline included in this repository. The Lambda indexes incoming events into Elasticsearch/OpenSearch and maintains `cart_state` documents.

Files of interest:
- Template: [aws/eventbridge_lambda_template.yaml](aws/eventbridge_lambda_template.yaml#L1)
- Example parameters: [aws/eventbridge_params.json](aws/eventbridge_params.json#L1)

Steps (SAM):

1. Install Python dependencies for local testing:
```bash
pip install -r requirements.txt
```

2. Build & deploy with SAM (example):
```bash
sam build
sam deploy --template-file aws/eventbridge_lambda_template.yaml \
  --stack-name AbandonedCartIngest \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides EsEndpoint=https://search-your-es.example.com CHECK_AT_MINUTES=30
```

3. Or use AWS CloudFormation with the example parameter file:
```bash
aws cloudformation create-stack --stack-name AbandonedCartIngest \
  --template-body file://aws/eventbridge_lambda_template.yaml \
  --parameters file://aws/eventbridge_params.json \
  --capabilities CAPABILITY_IAM
```

4. Post-deploy:
- Confirm the Lambda environment variables include `ES_ENDPOINT` and the chosen authentication method (`ES_API_KEY` or `ES_USERNAME`/`ES_PASSWORD`).
- Confirm `CHECK_AT_MINUTES` is set to the desired value.

5. Sending seed events:
- Ensure AWS credentials are configured (env or profile).
- Optionally set `EVENT_BUS_NAME` (default is `default`).

```bash
export AWS_PROFILE=your-profile
export EVENT_BUS_NAME=default
python scripts/seed_sample_data.py
```

Notes:
- The Lambda handler uses the `ES_ENDPOINT` environment variable to communicate with Elasticsearch/OpenSearch. If using API key authentication, set `ES_API_KEY` in the function environment. For basic auth, set `ES_USERNAME` and `ES_PASSWORD`.
- `CHECK_AT_MINUTES` controls how far ahead `check_at` is set for `cart_state` documents.

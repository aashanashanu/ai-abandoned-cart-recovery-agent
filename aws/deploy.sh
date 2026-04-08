#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="ai-abandoned-cart-recovery"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
REGION="${AWS_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Deploying Unified Stack (${ENVIRONMENT})..."

# Deploy CloudFormation stack
aws cloudformation deploy \
  --template-file "${SCRIPT_DIR}/stack.yml" \
  --stack-name "${STACK_NAME}" \
  --parameter-overrides \
    Environment="${ENVIRONMENT}" \
    ProjectName="${PROJECT_NAME}" \
  --capabilities CAPABILITY_NAMED_IAM \
  --region "${REGION}" \
  --tags \
    Project="${PROJECT_NAME}" \
    Environment="${ENVIRONMENT}"

echo "✅ CloudFormation stack deployed."

# Get bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='DecisionMatrixBucketName'].OutputValue" \
  --output text)

echo "📦 Uploading decision matrix to S3 bucket: ${BUCKET_NAME}..."

# Upload decision matrix JSON to S3
aws s3 cp \
  "${SCRIPT_DIR}/decision-matrix/decision-matrix.json" \
  "s3://${BUCKET_NAME}/decision-matrix.json" \
  --server-side-encryption AES256 \
  --region "${REGION}"

echo "✅ Decision matrix uploaded."

# Package and update Lambda function code
echo "📦 Packaging Lambda function..."
pushd "${SCRIPT_DIR}/lambda/decision_engine" > /dev/null
zip -r /tmp/decision-engine-lambda.zip handler.py
popd > /dev/null

LAMBDA_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='DecisionEngineLambdaName'].OutputValue" \
  --output text)

aws lambda update-function-code \
  --function-name "${LAMBDA_NAME}" \
  --zip-file fileb:///tmp/decision-engine-lambda.zip \
  --region "${REGION}"

echo "✅ Decision engine Lambda code updated."

# Package and deploy Recovery Action Lambda
echo "📦 Packaging Recovery Action Lambda..."
pushd "${SCRIPT_DIR}/lambda/recovery_action" > /dev/null
zip -r /tmp/recovery-action-lambda.zip handler.py
popd > /dev/null

RECOVERY_LAMBDA_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='RecoveryActionLambdaName'].OutputValue" \
  --output text)

aws lambda update-function-code \
  --function-name "${RECOVERY_LAMBDA_NAME}" \
  --zip-file fileb:///tmp/recovery-action-lambda.zip \
  --region "${REGION}"

echo "✅ Recovery action Lambda code updated."
echo "🎉 Deployment complete!"

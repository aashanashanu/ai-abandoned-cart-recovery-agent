#!/bin/bash
set -euo pipefail

ENVIRONMENT="${1:-dev}"
PROJECT_NAME="ai-abandoned-cart-recovery"
STACK_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
REGION="${AWS_REGION:-us-east-1}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
S3_BUCKET="${PROJECT_NAME}-cfn-artifacts-${REGION}"

echo "🚀 Deploying Unified Stack (${ENVIRONMENT})..."

# Create S3 bucket for CloudFormation artifacts if it doesn't exist
if ! aws s3 ls "s3://${S3_BUCKET}" --region "${REGION}" 2>/dev/null; then
  echo "📦 Creating S3 bucket for CloudFormation artifacts: ${S3_BUCKET}"
  aws s3 mb "s3://${S3_BUCKET}" --region "${REGION}"
fi

# Package SAM template (resolves CodeUri references and uploads to S3)
echo "📦 Packaging SAM template..."
PACKAGED_TEMPLATE="/tmp/packaged-${ENVIRONMENT}.yml"
aws cloudformation package \
  --template-file "${SCRIPT_DIR}/stack.yml" \
  --s3-bucket "${S3_BUCKET}" \
  --s3-prefix "cfn-deploy" \
  --output-template-file "${PACKAGED_TEMPLATE}" \
  --region "${REGION}"

# Deploy CloudFormation stack using packaged template
aws cloudformation deploy \
  --template-file "${PACKAGED_TEMPLATE}" \
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
  --sse AES256 \
  --region "${REGION}"

echo "✅ Decision matrix uploaded."

# Update Lambda function code with actual handlers
echo "📦 Updating Lambda function code..."

DECISION_LAMBDA_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='DecisionEngineLambdaName'].OutputValue" \
  --output text)

RECOVERY_LAMBDA_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='RecoveryActionLambdaName'].OutputValue" \
  --output text)

MCP_LAMBDA_NAME=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='McpServerLambdaName'].OutputValue" \
  --output text)

# Update Decision Engine Lambda
echo "  Updating decision engine..."
pushd "${SCRIPT_DIR}/lambda/decision_engine" > /dev/null
zip -r /tmp/decision-engine.zip handler.py
aws lambda update-function-code \
  --function-name "${DECISION_LAMBDA_NAME}" \
  --zip-file fileb:///tmp/decision-engine.zip \
  --region "${REGION}" > /dev/null
popd > /dev/null

# Update Recovery Action Lambda
echo "  Updating recovery action..."
pushd "${SCRIPT_DIR}/lambda/recovery_action" > /dev/null
zip -r /tmp/recovery-action.zip handler.py
aws lambda update-function-code \
  --function-name "${RECOVERY_LAMBDA_NAME}" \
  --zip-file fileb:///tmp/recovery-action.zip \
  --region "${REGION}" > /dev/null
popd > /dev/null

# Update MCP Server Lambda
echo "  Updating MCP server..."
pushd "${SCRIPT_DIR}/lambda/mcp_server" > /dev/null
zip -r /tmp/mcp-server.zip handler.py
aws lambda update-function-code \
  --function-name "${MCP_LAMBDA_NAME}" \
  --zip-file fileb:///tmp/mcp-server.zip \
  --region "${REGION}" > /dev/null
popd > /dev/null

echo "✅ Lambda code updated."

# Retrieve MCP Server URL and API Key
MCP_SERVER_URL=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='McpServerUrl'].OutputValue" \
  --output text)

MCP_API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${REGION}" \
  --query "Stacks[0].Outputs[?OutputKey=='McpApiKeyId'].OutputValue" \
  --output text)

MCP_API_KEY_VALUE=$(aws apigateway get-api-key \
  --api-key "${MCP_API_KEY_ID}" \
  --include-value \
  --region "${REGION}" \
  --query "value" \
  --output text)

echo ""
echo "========================================"
echo "  MCP Server Deployment Details"
echo "========================================"
echo "  URL:     ${MCP_SERVER_URL}"
echo "  API Key: ${MCP_API_KEY_VALUE}"
echo "========================================"
echo ""
echo "Test with:"
echo "  curl -X POST ${MCP_SERVER_URL} \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'x-api-key: ${MCP_API_KEY_VALUE}' \\"
echo "    -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{}}'"
echo ""

echo "🎉 Deployment complete!"

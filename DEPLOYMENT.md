# MCP Server – Deployment Summary

**Status**: ✅ Successfully deployed to AWS

## Endpoint Details

| Property | Value |
|----------|-------|
| **URL** | `https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp` |
| **API Key** | `LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl` |
| **Region** | `us-east-1` |
| **Environment** | `dev` |
| **Stack Name** | `ai-abandoned-cart-recovery-dev` |

## Available Tools

### 1. decision_engine
Determines the best recovery action for an abandoned cart based on:
- Customer segment (VIP / standard / high_fraud_risk)
- Abandonment reason (payment_failure / shipping_issue / browsing_abandonment / etc.)
- Cart value
- Fraud risk level

**Example Call:**
```bash
curl -X POST https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' \
  -d '{
    "jsonrpc":"2.0",
    "id":1,
    "method":"tools/call",
    "params":{
      "name":"decision_engine",
      "arguments":{
        "cart_id":"cart_001",
        "customer_id":"cust_42",
        "user_segment":"VIP",
        "abandonment_reason":"payment_failure",
        "cart_value":500.00,
        "fraud_risk":"low"
      }
    }
  }'
```

### 2. recovery_action
Sends recovery email via Amazon SES and publishes recovery history to EventBridge.

**Requires:** Output from decision_engine tool

**Example Call:**
```bash
curl -X POST https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' \
  -d '{
    "jsonrpc":"2.0",
    "id":2,
    "method":"tools/call",
    "params":{
      "name":"recovery_action",
      "arguments":{
        "cart_id":"cart_001",
        "customer_id":"cust_42",
        "email":"customer@example.com",
        "customer_name":"Jane Doe",
        "recommended_action":{
          "type":"discount",
          "discount":"15%",
          "message":"Complete your purchase and get 15% off!"
        }
      }
    }
  }'
```

## AWS Resources Created

- **MCP Server Lambda** – Handles JSON-RPC 2.0 requests, routes to tools
- **API Gateway REST API** – Public HTTPS endpoint with API key authentication
- **API Key & Usage Plan** – 100 req/s throttling, 10,000 req/day quota
- **Lambda Permissions** – Allow API Gateway → MCP Server, MCP → Tool Lambdas
- **CloudWatch Logs** – Centralized logging for all Lambda functions

## Authentication

Every request requires the API key in the `x-api-key` header:

```bash
curl -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' ...
```

## MCP Protocol Support

✅ JSON-RPC 2.0 compliance
✅ Methods: initialize, ping, tools/list, tools/call
✅ Notifications: notifications/initialized
✅ Batch requests support
✅ HTTP GET (health check)
✅ HTTP DELETE (session termination)
✅ CORS support

## MCP Client Configuration

```json
{
  "mcpServers": {
    "ai-abandoned-cart-recovery": {
      "url": "https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp",
      "transport": "streamable-http",
      "headers": {
        "x-api-key": "LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl"
      }
    }
  }
}
```

## Quick Tests

### Health Check
```bash
curl https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl'
```

### List Tools
```bash
curl -X POST https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### Initialize Handshake
```bash
curl -X POST https://85vaz0z5p1.execute-api.us-east-1.amazonaws.com/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'x-api-key: LUz0EXvKYJ80C3OOOK87x5EK2Sq6N1fk4ubFTEjl' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'
```

## Redeploy

To make changes and redeploy:

```bash
cd aws && ./deploy.sh dev
```

The deploy script will:
1. Package SAM template with all Lambda code
2. Deploy/update CloudFormation stack
3. Upload decision matrix to S3
4. Update Lambda function code
5. Print the endpoint URL and API key

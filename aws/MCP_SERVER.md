# MCP Server – Deployment & Usage Guide

## Overview

The MCP (Model Context Protocol) server exposes the **Decision Engine** and
**Recovery Action** Lambda functions as MCP tools over a Streamable HTTP
transport. An API Gateway REST API sits in front of the Lambda providing a
public HTTPS endpoint secured with an **API key**.

## Architecture

```
Client (LLM / Agent)
       │
       │  x-api-key header
       ▼
┌──────────────────────┐
│   API Gateway        │  POST /mcp  (JSON-RPC 2.0)
│   (API Key auth)     │  GET  /mcp  (health / server info)
└──────────┬───────────┘  DELETE /mcp (session termination)
           │
           ▼
┌──────────────────────┐
│  MCP Server Lambda   │  routes JSON-RPC methods
└──────────┬───────────┘
           │ lambda:InvokeFunction
     ┌─────┴──────┐
     ▼            ▼
┌──────────┐ ┌───────────────┐
│ Decision │ │ Recovery      │
│ Engine   │ │ Action        │
│ Lambda   │ │ Lambda        │
└──────────┘ └───────────────┘
```

## Deployed Resources

| Resource | Description |
|----------|-------------|
| `McpServerLambda` | Lambda that implements the MCP JSON-RPC server |
| `McpApi` | API Gateway REST API |
| `McpApiStage` | API Gateway stage (`v1` by default) |
| `McpApiKey` | API key for authentication |
| `McpApiUsagePlan` | Throttling & quota (100 req/s, 10 000/day) |

## Endpoint

After deployment the stack outputs:

- **`McpServerUrl`** – full URL, e.g.
  `https://<api-id>.execute-api.<region>.amazonaws.com/v1/mcp`
- **`McpApiKeyId`** – ID of the API key (retrieve the secret value via CLI)

## Authentication

Every request **must** include the API key in the `x-api-key` header:

```
x-api-key: <your-api-key-value>
```

Retrieve the key value after deployment:

```bash
# From deploy.sh output, or manually:
API_KEY_ID=$(aws cloudformation describe-stacks \
  --stack-name ai-abandoned-cart-recovery-dev \
  --query "Stacks[0].Outputs[?OutputKey=='McpApiKeyId'].OutputValue" \
  --output text)

aws apigateway get-api-key \
  --api-key "$API_KEY_ID" \
  --include-value \
  --query "value" \
  --output text
```

## MCP Protocol Methods

| Method | Description |
|--------|-------------|
| `initialize` | Handshake – returns server info & capabilities |
| `ping` | Health check |
| `tools/list` | List available tools |
| `tools/call` | Execute a tool (decision_engine or recovery_action) |
| `notifications/initialized` | Client notification (no response) |

## Usage Examples

### 1. Initialize

```bash
curl -X POST "$MCP_SERVER_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {}
  }'
```

### 2. List Tools

```bash
curl -X POST "$MCP_SERVER_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

### 3. Call Decision Engine

```bash
curl -X POST "$MCP_SERVER_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "decision_engine",
      "arguments": {
        "cart_id": "cart_001",
        "customer_id": "cust_42",
        "user_segment": "VIP",
        "abandonment_reason": "payment_failure",
        "cart_value": 450.00,
        "fraud_risk": "low"
      }
    }
  }'
```

### 4. Call Recovery Action

```bash
curl -X POST "$MCP_SERVER_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MCP_API_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "id": 4,
    "method": "tools/call",
    "params": {
      "name": "recovery_action",
      "arguments": {
        "cart_id": "cart_001",
        "customer_id": "cust_42",
        "email": "customer@example.com",
        "customer_name": "Jane Doe",
        "recommended_action": {
          "type": "discount",
          "discount": "15%",
          "message": "Complete your purchase and get 15% off!"
        }
      }
    }
  }'
```

### 5. Batch Request

```bash
curl -X POST "$MCP_SERVER_URL" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $MCP_API_KEY" \
  -d '[
    {"jsonrpc":"2.0","id":1,"method":"initialize","params":{}},
    {"jsonrpc":"2.0","method":"notifications/initialized"},
    {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
  ]'
```

### 6. Health Check (GET)

```bash
curl "$MCP_SERVER_URL" \
  -H "x-api-key: $MCP_API_KEY"
```

## MCP Client Configuration

To connect an MCP-compatible client (e.g. Claude Desktop, VS Code Copilot):

```json
{
  "mcpServers": {
    "ai-abandoned-cart-recovery": {
      "url": "https://<api-id>.execute-api.<region>.amazonaws.com/v1/mcp",
      "transport": "streamable-http",
      "headers": {
        "x-api-key": "<your-api-key-value>"
      }
    }
  }
}
```

## Deployment

```bash
cd aws
./deploy.sh dev
```

The deploy script will:
1. Deploy/update the CloudFormation stack
2. Upload the decision matrix to S3
3. Package and deploy all Lambda functions (including the MCP server)
4. Print the MCP server URL and API key value

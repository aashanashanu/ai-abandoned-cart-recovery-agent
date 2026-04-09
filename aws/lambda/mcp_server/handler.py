"""
MCP (Model Context Protocol) Server – AWS Lambda Handler.

Implements the MCP JSON-RPC 2.0 protocol over Streamable HTTP transport.
Exposes the Decision Engine and Recovery Action Lambdas as MCP tools.

Authentication is handled upstream by API Gateway API-key enforcement.
"""

import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda")

DECISION_ENGINE_FUNCTION = os.environ.get("DECISION_ENGINE_FUNCTION", "")
RECOVERY_ACTION_FUNCTION = os.environ.get("RECOVERY_ACTION_FUNCTION", "")

MCP_SERVER_NAME = "ai-abandoned-cart-recovery-mcp"
MCP_SERVER_VERSION = "1.0.0"
MCP_PROTOCOL_VERSION = "2025-03-26"

# ── MCP Tool Definitions ────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "decision_engine",
        "description": (
            "Determine the best recovery action for an abandoned cart based on "
            "customer segment, abandonment reason, cart value, and fraud risk. "
            "Returns a recommended action with type, discount, and message."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cart_id": {
                    "type": "string",
                    "description": "Unique identifier for the abandoned cart",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Unique identifier for the customer",
                },
                "user_segment": {
                    "type": "string",
                    "description": "Customer segment: VIP, standard, high_fraud_risk",
                    "enum": ["VIP", "standard", "high_fraud_risk"],
                },
                "abandonment_reason": {
                    "type": "string",
                    "description": (
                        "Root cause of abandonment: payment_failure, shipping_issue, "
                        "browsing_abandonment, performance_latency, unknown"
                    ),
                    "enum": [
                        "payment_failure",
                        "shipping_issue",
                        "browsing_abandonment",
                        "performance_latency",
                        "unknown",
                    ],
                },
                "cart_value": {
                    "type": "number",
                    "description": "Total value of the abandoned cart",
                },
                "fraud_risk": {
                    "type": "string",
                    "description": "Customer fraud risk level: low, medium, high",
                    "enum": ["low", "medium", "high"],
                },
            },
            "required": ["cart_id", "customer_id", "user_segment", "abandonment_reason"],
        },
    },
    {
        "name": "recovery_action",
        "description": (
            "Send a recovery email via Amazon SES and publish a recovery_history "
            "event to EventBridge. Use this after the decision engine has determined "
            "the recommended action."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cart_id": {
                    "type": "string",
                    "description": "Unique identifier for the abandoned cart",
                },
                "customer_id": {
                    "type": "string",
                    "description": "Unique identifier for the customer",
                },
                "email": {
                    "type": "string",
                    "description": "Customer email address to send recovery message to",
                },
                "customer_name": {
                    "type": "string",
                    "description": "Customer display name (optional, used in email greeting)",
                },
                "recommended_action": {
                    "type": "object",
                    "description": "Recovery action determined by the decision engine",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": (
                                "Action type: payment_retry, discount, free_shipping, "
                                "reminder, reminder_only, blocked"
                            ),
                            "enum": [
                                "payment_retry",
                                "discount",
                                "free_shipping",
                                "reminder",
                                "reminder_only",
                                "blocked",
                            ],
                        },
                        "discount": {
                            "type": "string",
                            "description": "Discount amount if applicable (e.g. '15%', '10%')",
                        },
                        "message": {
                            "type": "string",
                            "description": "Recovery message to include in the email",
                        },
                    },
                    "required": ["type", "message"],
                },
            },
            "required": ["cart_id", "customer_id", "email", "recommended_action"],
        },
    },
]

# Tool name → Lambda function name mapping
TOOL_FUNCTION_MAP = {
    "decision_engine": DECISION_ENGINE_FUNCTION,
    "recovery_action": RECOVERY_ACTION_FUNCTION,
}

# ── Helpers ──────────────────────────────────────────────────────────────────


def _jsonrpc_response(id, result):
    """Build a successful JSON-RPC 2.0 response."""
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _jsonrpc_error(id, code, message, data=None):
    """Build a JSON-RPC 2.0 error response."""
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": id, "error": err}


def _invoke_lambda(function_name, payload):
    """Synchronously invoke a Lambda function and return its response body."""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload),
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        return response_payload
    except ClientError as exc:
        logger.error(f"Lambda invoke error ({function_name}): {exc}")
        raise


# ── JSON-RPC Method Handlers ────────────────────────────────────────────────


def _handle_initialize(id, _params):
    """Respond to the MCP initialize handshake."""
    return _jsonrpc_response(
        id,
        {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
            },
        },
    )


def _handle_ping(id, _params):
    """Respond to an MCP ping."""
    return _jsonrpc_response(id, {})


def _handle_tools_list(id, _params):
    """Return the list of available MCP tools."""
    return _jsonrpc_response(id, {"tools": TOOLS})


def _handle_tools_call(id, params):
    """Execute an MCP tool by invoking the corresponding Lambda."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name not in TOOL_FUNCTION_MAP:
        return _jsonrpc_error(
            id,
            -32602,
            f"Unknown tool: {tool_name}",
            {"available_tools": list(TOOL_FUNCTION_MAP.keys())},
        )

    function_name = TOOL_FUNCTION_MAP[tool_name]
    if not function_name:
        return _jsonrpc_error(
            id,
            -32603,
            f"Lambda function not configured for tool: {tool_name}",
        )

    try:
        lambda_response = _invoke_lambda(function_name, arguments)

        # Parse the body if the Lambda returned the standard API Gateway shape
        body = lambda_response
        if isinstance(lambda_response, dict) and "body" in lambda_response:
            try:
                body = json.loads(lambda_response["body"])
            except (json.JSONDecodeError, TypeError):
                body = lambda_response["body"]

        status_code = lambda_response.get("statusCode", 200) if isinstance(lambda_response, dict) else 200
        is_error = status_code >= 400

        return _jsonrpc_response(
            id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(body, indent=2),
                    }
                ],
                "isError": is_error,
            },
        )

    except Exception as exc:
        logger.error(f"Tool execution error ({tool_name}): {exc}")
        return _jsonrpc_response(
            id,
            {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({"error": str(exc)}),
                    }
                ],
                "isError": True,
            },
        )


# Method routing table
METHOD_HANDLERS = {
    "initialize": _handle_initialize,
    "ping": _handle_ping,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
}

# Notification methods (no response expected)
NOTIFICATION_METHODS = {"notifications/initialized", "notifications/cancelled"}

# ── Main Lambda Handler ─────────────────────────────────────────────────────


def handler(event, context):
    """
    Lambda handler for the MCP server.

    Accepts JSON-RPC 2.0 requests via API Gateway (POST).
    Also supports GET for SSE session initialization (returns 405 for stateless mode)
    and DELETE for session termination.
    """
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "POST")

    # ── GET: Health check / SSE not supported in stateless mode ──
    if http_method == "GET":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({
                "server": MCP_SERVER_NAME,
                "version": MCP_SERVER_VERSION,
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "status": "healthy",
                "transport": "streamable-http",
                "tools": [t["name"] for t in TOOLS],
            }),
        }

    # ── DELETE: Session termination ──
    if http_method == "DELETE":
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"status": "session_terminated"}),
        }

    # ── OPTIONS: CORS preflight ──
    if http_method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key, Mcp-Session-Id",
                "Access-Control-Max-Age": "86400",
            },
            "body": "",
        }

    # ── POST: JSON-RPC 2.0 request ──
    try:
        body = event.get("body", "")
        if isinstance(body, str):
            body = json.loads(body)
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(
                _jsonrpc_error(None, -32700, "Parse error: invalid JSON")
            ),
        }

    # Support batch requests (array of JSON-RPC messages)
    is_batch = isinstance(body, list)
    requests = body if is_batch else [body]

    responses = []
    for req in requests:
        jsonrpc = req.get("jsonrpc")
        method = req.get("method")
        params = req.get("params", {})
        req_id = req.get("id")

        # Validate JSON-RPC version
        if jsonrpc != "2.0":
            responses.append(
                _jsonrpc_error(req_id, -32600, "Invalid Request: jsonrpc must be '2.0'")
            )
            continue

        # Handle notifications (no id → no response)
        if req_id is None and method in NOTIFICATION_METHODS:
            logger.info(f"Received notification: {method}")
            continue

        # Route to handler
        handler_fn = METHOD_HANDLERS.get(method)
        if handler_fn is None:
            responses.append(
                _jsonrpc_error(req_id, -32601, f"Method not found: {method}")
            )
            continue

        result = handler_fn(req_id, params)
        if result is not None:
            responses.append(result)

    # Build HTTP response
    if not responses:
        # All messages were notifications – return 204
        return {
            "statusCode": 204,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": "",
        }

    response_body = responses if is_batch else responses[0]

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Api-Key, Mcp-Session-Id",
        },
        "body": json.dumps(response_body),
    }

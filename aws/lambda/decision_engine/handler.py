import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

DECISION_BUCKET = os.environ.get("DECISION_BUCKET", "")
DECISION_MATRIX_KEY = "decision-matrix.json"

FALLBACK_ACTION = {
    "type": "reminder",
    "message": "Complete your purchase"
}


def console_error(message):
    """Log errors using console.error equivalent."""
    logger.error(message)


def fetch_decision_matrix():
    """Fetch and parse the decision matrix JSON from S3."""
    try:
        response = s3_client.get_object(
            Bucket=DECISION_BUCKET,
            Key=DECISION_MATRIX_KEY
        )
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)
    except ClientError as e:
        console_error(f"S3 ClientError fetching decision matrix: {e}")
        raise
    except json.JSONDecodeError as e:
        console_error(f"Failed to parse decision matrix JSON: {e}")
        raise


def resolve_action(matrix, user_segment, abandonment_reason, cart_value=None):
    """
    Determine the correct action from the decision matrix based on
    user_segment and abandonment_reason.

    Falls back to 'default' segment if user_segment not found.
    Returns a fallback action if abandonment_reason not found.
    """
    segments = matrix.get("segments", {})

    # Normalize segment key
    segment_key = user_segment.lower().replace(" ", "_") if user_segment else "default"

    # Fallback to 'default' if segment not found
    if segment_key not in segments:
        console_error(f"Segment '{segment_key}' not found. Falling back to 'default'.")
        segment_key = "default"

    segment_data = segments.get(segment_key, {})

    # Normalize reason key
    reason_key = abandonment_reason.lower().replace(" ", "_") if abandonment_reason else None

    # Check for high cart value override (VIP > $500, Standard > $300)
    if reason_key and reason_key != "payment_failure" and cart_value is not None:
        high_cart_action = segment_data.get("high_cart_value")
        if high_cart_action:
            threshold = high_cart_action.get("cart_value_threshold", 0)
            if cart_value > threshold:
                return {
                    "type": high_cart_action.get("type", "reminder"),
                    "discount": high_cart_action.get("discount"),
                    "message": high_cart_action.get("message", ""),
                    "free_shipping": high_cart_action.get("free_shipping", False)
                }

    # Return fallback if abandonment_reason not found
    if not reason_key or reason_key not in segment_data:
        console_error(
            f"Abandonment reason '{reason_key}' not found for segment '{segment_key}'. "
            f"Returning fallback action."
        )
        return FALLBACK_ACTION.copy()

    action_data = segment_data[reason_key]

    return {
        "type": action_data.get("type", "reminder"),
        "discount": action_data.get("discount"),
        "message": action_data.get("message", ""),
        "free_shipping": action_data.get("free_shipping", False)
    }


def handler(event, context):
    """
    Lambda handler for the decision engine.

    Expected event payload (from detect_abandonment_reasons workflow):
    {
        "cart_id": "string",
        "customer_id": "string",
        "user_segment": "VIP | standard | high_fraud_risk",
        "abandonment_reason": "payment_failure | shipping_issue | browsing_abandonment",
        "cart_value": 450.00,
        "fraud_risk": "low | medium | high"
    }
    """
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        cart_id = event.get("cart_id", "unknown")
        user_segment = event.get("user_segment", "default")
        abandonment_reason = event.get("abandonment_reason", "")
        cart_value = event.get("cart_value")
        fraud_risk = event.get("fraud_risk", "low")

        # Override segment for high fraud risk
        if fraud_risk and fraud_risk.lower() == "high":
            user_segment = "high_fraud_risk"

        # Fetch decision matrix from S3
        matrix = fetch_decision_matrix()

        # Resolve the recommended action
        recommended_action = resolve_action(
            matrix=matrix,
            user_segment=user_segment,
            abandonment_reason=abandonment_reason,
            cart_value=cart_value
        )

        # Build response
        result = {
            "statusCode": 200,
            "body": json.dumps({
                "cart_id": cart_id,
                "recommended_action": {
                    "type": recommended_action.get("type"),
                    "discount": recommended_action.get("discount"),
                    "message": recommended_action.get("message")
                }
            })
        }

        logger.info(f"Decision engine result: {json.dumps(result)}")
        return result

    except Exception as e:
        console_error(f"Decision engine error: {e}")

        # Return fallback response on failure
        return {
            "statusCode": 500,
            "body": json.dumps({
                "cart_id": event.get("cart_id", "unknown"),
                "recommended_action": FALLBACK_ACTION
            })
        }

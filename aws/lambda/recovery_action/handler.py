import json
import os
import logging
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses_client = boto3.client("ses")
events_client = boto3.client("events")

SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "")
EVENT_BUS_NAME = os.environ.get("EVENT_BUS_NAME", "")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev")


def _now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _send_email(recipient, subject, body_html, body_text):
    """Send a recovery email via Amazon SES."""
    if not SENDER_EMAIL:
        logger.warning("SENDER_EMAIL not configured – skipping email send")
        return {"status": "skipped", "reason": "SENDER_EMAIL not set"}

    if not recipient:
        logger.warning("No recipient email provided – skipping email send")
        return {"status": "skipped", "reason": "no recipient"}

    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": body_html, "Charset": "UTF-8"},
                    "Text": {"Data": body_text, "Charset": "UTF-8"},
                },
            },
        )
        message_id = response.get("MessageId", "")
        logger.info(f"SES email sent to {recipient}, MessageId={message_id}")
        return {"status": "sent", "channel": "email", "message_id": message_id}
    except ClientError as e:
        logger.error(f"SES send_email failed: {e}")
        return {"status": "failed", "channel": "email", "error": str(e)}


def _build_email_content(action_type, message, discount, cart_id, customer_name=None):
    """Build HTML and plain-text email bodies based on the recovery action."""
    name = customer_name or "Valued Customer"
    subject = "Don't forget your cart!"

    if action_type == "discount":
        subject = f"Here's {discount} off to complete your order!"
    elif action_type == "free_shipping":
        subject = "Free shipping on your cart – limited time!"
    elif action_type == "payment_retry":
        subject = "Let's try that payment again"
    elif action_type == "reminder":
        subject = "You left something behind!"

    body_text = f"Hi {name},\n\n{message}\n\nCart ID: {cart_id}\n\nThank you!"

    body_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #333;">Hi {name},</h2>
        <p style="font-size: 16px; color: #555;">{message}</p>
        {"<p style='font-size: 18px; color: #e74c3c; font-weight: bold;'>Use discount: " + discount + "</p>" if discount else ""}
        <p style="margin-top: 20px;">
            <a href="#" style="background: #3498db; color: white; padding: 12px 24px;
               text-decoration: none; border-radius: 4px; font-size: 16px;">
               Complete Your Purchase
            </a>
        </p>
        <p style="font-size: 12px; color: #999; margin-top: 30px;">Cart reference: {cart_id}</p>
    </body>
    </html>
    """

    return subject, body_html, body_text


def _publish_recovery_history(cart_id, customer_id, action, send_result, recovery_id):
    """Publish a recovery_history event to EventBridge for indexing."""
    if not EVENT_BUS_NAME:
        logger.warning("EVENT_BUS_NAME not configured – skipping recovery history event")
        return

    detail = {
        "_index": "recovery_history",
        "_id": recovery_id,
        "_source": {
            "@timestamp": _now_iso(),
            "recovery_id": recovery_id,
            "cart_id": cart_id,
            "customer_id": customer_id,
            "action": action,
            "channel": send_result.get("channel", "email"),
            "send_status": send_result.get("status", "unknown"),
            "message_id": send_result.get("message_id"),
            "sent_at": _now_iso(),
            "status": "sent" if send_result.get("status") == "sent" else "failed",
        },
    }

    try:
        response = events_client.put_events(
            Entries=[
                {
                    "Source": "ai-abandoned-cart",
                    "DetailType": "recovery_history",
                    "Detail": json.dumps(detail),
                    "EventBusName": EVENT_BUS_NAME,
                }
            ]
        )
        failed = response.get("FailedEntryCount", 0)
        if failed > 0:
            logger.error(f"EventBridge put_events failed: {response}")
        else:
            logger.info(f"Recovery history event published for cart {cart_id}")
    except ClientError as e:
        logger.error(f"EventBridge put_events error: {e}")


def handler(event, context):
    """
    Lambda handler for recovery action execution.

    Expected event payload (from decision engine or MCP tool call):
    {
        "cart_id": "string",
        "customer_id": "string",
        "email": "string",
        "customer_name": "string (optional)",
        "recommended_action": {
            "type": "payment_retry | discount | free_shipping | reminder | reminder_only | blocked",
            "discount": "15% (optional)",
            "message": "string"
        }
    }
    """
    try:
        logger.info(f"Recovery action received: {json.dumps(event)}")

        cart_id = event.get("cart_id", "unknown")
        customer_id = event.get("customer_id", "unknown")
        email = event.get("email", "")
        customer_name = event.get("customer_name")
        recommended_action = event.get("recommended_action", {})

        action_type = recommended_action.get("type", "reminder")
        message = recommended_action.get("message", "Complete your purchase")
        discount = recommended_action.get("discount")

        recovery_id = f"rec_{uuid.uuid4().hex[:12]}"

        # Blocked actions – do nothing
        if action_type == "blocked":
            logger.info(f"Cart {cart_id} blocked – no recovery action taken")
            result = {
                "statusCode": 200,
                "body": json.dumps({
                    "cart_id": cart_id,
                    "recovery_id": recovery_id,
                    "action_taken": "blocked",
                    "send_result": {"status": "blocked", "channel": "none"},
                }),
            }
            _publish_recovery_history(
                cart_id, customer_id,
                {"type": action_type, "message": message, "discount": discount},
                {"status": "blocked", "channel": "none"},
                recovery_id,
            )
            return result

        # Build email content
        subject, body_html, body_text = _build_email_content(
            action_type, message, discount, cart_id, customer_name
        )

        # Send via SES
        send_result = _send_email(email, subject, body_html, body_text)

        # Publish recovery history event to EventBridge
        _publish_recovery_history(
            cart_id, customer_id,
            {"type": action_type, "message": message, "discount": discount},
            send_result,
            recovery_id,
        )

        result = {
            "statusCode": 200,
            "body": json.dumps({
                "cart_id": cart_id,
                "recovery_id": recovery_id,
                "action_taken": action_type,
                "send_result": send_result,
            }),
        }

        logger.info(f"Recovery action result: {json.dumps(result)}")
        return result

    except Exception as e:
        logger.error(f"Recovery action error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "cart_id": event.get("cart_id", "unknown"),
                "error": str(e),
            }),
        }

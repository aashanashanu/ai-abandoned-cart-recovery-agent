from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from src.models.schemas import (
    AbandonedCartCandidate,
    AbandonmentDiagnosis,
    ActionOutcomeStats,
    CustomerProfile,
    RecoveryAction,
)


@dataclass(frozen=True)
class PolicyDecision:
    action: RecoveryAction
    rationale: str


def _best_action_from_history(
    stats: List[ActionOutcomeStats],
    allowed: set[str],
) -> Optional[str]:
    best_type = None
    best_rate = -1.0

    for s in stats:
        if s.action_type not in allowed:
            continue
        if s.success_rate > best_rate:
            best_rate = s.success_rate
            best_type = s.action_type

    return best_type


def decide_recovery_action(
    *,
    cart: AbandonedCartCandidate,
    diagnosis: AbandonmentDiagnosis,
    customer: CustomerProfile,
    similar_stats: List[ActionOutcomeStats],
) -> PolicyDecision:
    allowed = {"discount", "free_shipping", "reminder", "payment_retry"}

    if customer.fraud_risk == "high":
        allowed.discard("discount")
        allowed.discard("free_shipping")

    preferred_channel = customer.preferred_channel

    if diagnosis.root_cause == "payment_failure":
        if "payment_retry" in allowed:
            chosen = "payment_retry"
            action = RecoveryAction(
                type="payment_retry",
                channel=preferred_channel,
                template="retry_payment",
                metadata={"priority": "high"},
            )
            return PolicyDecision(
                action=action,
                rationale="Payment signals indicate a failure; retrying payment is the least-discounting recovery path.",
            )

    if diagnosis.root_cause == "performance_latency":
        if "reminder" in allowed:
            action = RecoveryAction(
                type="reminder",
                channel=preferred_channel,
                template="supportive_reminder",
                metadata={"offer_support": True},
            )
            return PolicyDecision(
                action=action,
                rationale="Session performance signals are degraded; a low-friction reminder + support is preferred over discounts.",
            )

    if diagnosis.root_cause == "pricing_shipping":
        best = _best_action_from_history(similar_stats, allowed)
        if best == "free_shipping" and "free_shipping" in allowed:
            action = RecoveryAction(
                type="free_shipping",
                channel=preferred_channel,
                template="free_shipping_offer",
                free_shipping=True,
            )
            return PolicyDecision(
                action=action,
                rationale="Historical recoveries for pricing/shipping issues perform well with free shipping.",
            )

        if "discount" in allowed:
            discount = 10.0 if customer.segment != "vip" else 12.5
            action = RecoveryAction(
                type="discount",
                channel=preferred_channel,
                template="discount_offer",
                discount_percent=discount,
                metadata={"reason": "shipping_or_price_sensitivity"},
            )
            return PolicyDecision(
                action=action,
                rationale="Price/shipping sensitivity detected; discounting can reduce total cost perception.",
            )

    best = _best_action_from_history(similar_stats, allowed)
    if best in {"discount", "free_shipping", "reminder", "payment_retry"}:
        if best == "free_shipping":
            action = RecoveryAction(
                type="free_shipping",
                channel=preferred_channel,
                template="free_shipping_offer",
                free_shipping=True,
            )
            return PolicyDecision(
                action=action,
                rationale="Similarity search indicates free shipping yields the highest success rate for comparable cases.",
            )

        if best == "discount" and "discount" in allowed:
            discount = 7.5 if customer.segment != "vip" else 10.0
            action = RecoveryAction(
                type="discount",
                channel=preferred_channel,
                template="discount_offer",
                discount_percent=discount,
            )
            return PolicyDecision(
                action=action,
                rationale="Similarity search indicates a discount yields the highest success rate for comparable cases.",
            )

        if best == "payment_retry" and "payment_retry" in allowed:
            action = RecoveryAction(
                type="payment_retry",
                channel=preferred_channel,
                template="retry_payment",
            )
            return PolicyDecision(
                action=action,
                rationale="Similarity search indicates payment retry yields the highest success rate for comparable cases.",
            )

        action = RecoveryAction(
            type="reminder",
            channel=preferred_channel,
            template="simple_reminder",
        )
        return PolicyDecision(
            action=action,
            rationale="Similarity search indicates reminders are most effective for comparable cases.",
        )

    if customer.segment == "vip" and "discount" in allowed and cart.cart_value >= 75:
        action = RecoveryAction(
            type="discount",
            channel=preferred_channel,
            template="discount_offer",
            discount_percent=10.0,
        )
        return PolicyDecision(
            action=action,
            rationale="VIP segment with high cart value; applying a modest discount increases conversion probability.",
        )

    action = RecoveryAction(
        type="reminder",
        channel=preferred_channel,
        template="simple_reminder",
    )
    return PolicyDecision(
        action=action,
        rationale="Defaulting to a reminder due to insufficient evidence for a stronger intervention.",
    )

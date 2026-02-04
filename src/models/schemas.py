from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


RootCause = Literal[
    "payment_failure",
    "performance_latency",
    "checkout_friction",
    "pricing_shipping",
    "unknown",
]

RecoveryActionType = Literal[
    "discount",
    "free_shipping",
    "reminder",
    "payment_retry",
]

ChannelType = Literal["email", "push", "sms"]


class AbandonedCartCandidate(BaseModel):
    cart_id: str
    customer_id: str
    session_id: Optional[str] = None
    last_seen: datetime
    cart_value: float = 0.0
    currency: str = "USD"
    device_type: Optional[str] = None


class DetectAbandonedCartsRequest(BaseModel):
    lookback_minutes: int = Field(1440, ge=1, le=43200)
    abandonment_minutes: int = Field(30, ge=5, le=1440)
    max_candidates: int = Field(20, ge=1, le=200)


class DetectAbandonedCartsResponse(BaseModel):
    candidates: List[AbandonedCartCandidate]


class AnalyzeAbandonmentRequest(BaseModel):
    cart_id: str


class AbandonmentDiagnosis(BaseModel):
    root_cause: RootCause
    signals: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class AnalyzeAbandonmentResponse(BaseModel):
    cart_id: str
    diagnosis: AbandonmentDiagnosis


class GetCustomerProfileRequest(BaseModel):
    customer_id: str


class CustomerProfile(BaseModel):
    customer_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    push_token: Optional[str] = None
    segment: str = "standard"
    lifetime_value: float = 0.0
    preferred_channel: ChannelType = "email"
    fraud_risk: Literal["low", "medium", "high"] = "low"
    locale: Optional[str] = None
    timezone: Optional[str] = None


class GetCustomerProfileResponse(BaseModel):
    profile: CustomerProfile


class SimilarityQuery(BaseModel):
    root_cause: RootCause
    segment: str
    cart_value: float


class ActionOutcomeStats(BaseModel):
    action_type: RecoveryActionType
    total: int
    recovered: int
    success_rate: float
    avg_revenue_recovered: float = 0.0


class FindSimilarAbandonmentsRequest(BaseModel):
    similarity: SimilarityQuery
    lookback_days: int = Field(180, ge=7, le=730)
    size: int = Field(20, ge=1, le=100)


class FindSimilarAbandonmentsResponse(BaseModel):
    stats: List[ActionOutcomeStats]
    examples: List[Dict[str, Any]] = Field(default_factory=list)


class DecideRecoveryActionRequest(BaseModel):
    cart: AbandonedCartCandidate
    diagnosis: AbandonmentDiagnosis
    customer: CustomerProfile
    similar_stats: List[ActionOutcomeStats] = Field(default_factory=list)


class RecoveryAction(BaseModel):
    type: RecoveryActionType
    channel: ChannelType
    template: str
    discount_percent: float = 0.0
    free_shipping: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DecideRecoveryActionResponse(BaseModel):
    action: RecoveryAction
    rationale: str


class TriggerRecoveryActionRequest(BaseModel):
    cart: AbandonedCartCandidate
    customer: CustomerProfile
    action: RecoveryAction


class TriggerRecoveryActionResponse(BaseModel):
    status: Literal["sent", "skipped", "failed"]
    message_id: Optional[str] = None
    channel: Optional[ChannelType] = None


class RecordRecoveryAttemptRequest(BaseModel):
    cart: AbandonedCartCandidate
    customer: CustomerProfile
    diagnosis: AbandonmentDiagnosis
    action: RecoveryAction
    sent_at: datetime


class RecordRecoveryAttemptResponse(BaseModel):
    recovery_id: str

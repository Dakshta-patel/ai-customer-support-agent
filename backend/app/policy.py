"""Deterministic NovaCart policy classification and escalation rules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PolicyCategory(str, Enum):
    EMPTY = "empty"
    REFUND_RETURN = "refund_return"
    ORDER = "order"
    DELIVERY = "delivery"
    ACCOUNT_SECURITY = "account_security"
    PAYMENT = "payment"
    HUMAN_SUPPORT = "human_support"
    UNCLEAR = "unclear"


@dataclass(frozen=True)
class PolicyDecision:
    should_escalate: bool
    escalation_reason: str | None
    policy_category: PolicyCategory
    rule_match: str
    confidence: str


def _decision(
    category: PolicyCategory,
    rule_match: str,
    confidence: str,
    *,
    should_escalate: bool = False,
    reason: str | None = None,
) -> PolicyDecision:
    if should_escalate and reason is None:
        raise ValueError("Escalated decisions require a reason")
    if not should_escalate:
        reason = None
    return PolicyDecision(
        should_escalate=should_escalate,
        escalation_reason=reason,
        policy_category=category,
        rule_match=rule_match,
        confidence=confidence,
    )


def _contains_any(query: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in query for phrase in phrases)


def classify_policy(query: str) -> PolicyDecision:
    """Classify a customer request using ordered, deterministic policy rules."""

    normalized_query = " ".join(query.lower().split())
    if not normalized_query:
        return _decision(PolicyCategory.EMPTY, "empty_query", "high")

    # Higher-risk account and payment rules take precedence over ordinary topics.
    if _contains_any(
        normalized_query,
        (
            "account takeover",
            "someone accessed my account",
            "unfamiliar contact detail",
            "unfamiliar contact information",
            "unfamiliar order on my account",
            "i shared my password",
            "shared my password",
            "shared my otp",
            "shared an otp",
            "bypass account verification",
            "bypass verification",
            "cannot prove account ownership",
            "can't prove account ownership",
        ),
    ) or (
        _contains_any(normalized_query, ("lost access", "can't access", "cannot access"))
        and _contains_any(normalized_query, ("ownership", "recover", "recovery", "registered email", "phone"))
    ):
        return _decision(
            PolicyCategory.ACCOUNT_SECURITY,
            "account_security_compromise",
            "high",
            should_escalate=True,
            reason="The request involves account security or ownership verification.",
        )

    if _contains_any(
        normalized_query,
        (
            "payment fraud",
            "payment was unauthorized",
            "unauthorized payment",
            "unauthorized charge",
            "duplicate payment capture",
            "duplicate payment",
            "payment deducted but no order",
            "payment was deducted but no order",
            "money deducted but no order",
            "money was deducted but no order",
            "money was deducted but there is no order",
            "payment credential",
            "shared my cvv",
            "shared my full card",
            "payment and order records conflict",
            "payment does not match the order",
        ),
    ):
        return _decision(
            PolicyCategory.PAYMENT,
            "high_risk_payment_issue",
            "high",
            should_escalate=True,
            reason="The request involves a potentially unauthorized or mismatched payment.",
        )

    if _contains_any(
        normalized_query,
        (
            "need a support agent",
            "contact support",
            "reviewed by a human",
            "reviewed by human",
            "speak to a human representative",
            "speak with a human representative",
            "talk to a human",
        ),
    ):
        return _decision(
            PolicyCategory.HUMAN_SUPPORT,
            "explicit_human_support_request",
            "high",
            should_escalate=True,
            reason="The customer explicitly requested review by NovaCart support.",
        )

    if _contains_any(
        normalized_query,
        (
            "tracking stopped",
            "tracking has stopped",
            "no tracking movement",
            "tracking no movement",
            "delivered but missing",
            "marked delivered but missing",
            "marked delivered but is missing",
            "parcel was marked delivered but is missing",
            "parcel is missing",
            "package is missing",
            "repeated delivery attempts failed",
            "delivery attempts keep failing",
            "address was compromised",
            "risky redirect",
            "unsafe redirect",
        ),
    ):
        return _decision(
            PolicyCategory.DELIVERY,
            "delivery_exception_requires_review",
            "high",
            should_escalate=True,
            reason="The delivery issue requires NovaCart support review.",
        )

    if _contains_any(
        normalized_query,
        (
            "dispute my damaged item claim",
            "disputed damage claim",
            "disputed defective claim",
            "return was lost after documented delivery",
            "return lost after delivery",
            "return outside the 30 day window",
            "return after 30 days exception",
            "return after 30 days",
            "outside the return window exception",
            "dispute the return inspection",
            "inspection decision is wrong",
            "refund is missing after the expected posting period",
            "refund still missing after processing",
            "original payment method is closed",
            "original payment method is unavailable",
            "category restriction is unclear",
            "unclear category restriction",
        ),
    ):
        return _decision(
            PolicyCategory.REFUND_RETURN,
            "return_or_refund_exception",
            "high",
            should_escalate=True,
            reason="The return or refund issue requires NovaCart support review.",
        )

    if _contains_any(
        normalized_query,
        (
            "disputed cancellation",
            "cancellation status is wrong",
            "duplicate orders",
            "duplicate order",
            "payment captured but no order record",
            "conflicting order records",
            "order records conflict",
            "risky address change",
            "unsafe address change",
        ),
    ):
        return _decision(
            PolicyCategory.ORDER,
            "order_status_or_record_conflict",
            "high",
            should_escalate=True,
            reason="The order issue requires NovaCart support review.",
        )

    if _contains_any(
        normalized_query,
        ("payment method", "payment failed", "payment fail", "payment is pending", "pending payment", "pay with upi", "net banking"),
    ):
        return _decision(PolicyCategory.PAYMENT, "ordinary_payment_question", "medium")

    if _contains_any(
        normalized_query,
        (
            "return window",
            "return eligibility",
            "return shipping",
            "shipping cost for a return",
            "refund timing",
            "where will my refund",
            "refund destination",
            "damaged item",
            "defective item",
            "return an item",
            "refund for my order",
        ),
    ):
        return _decision(PolicyCategory.REFUND_RETURN, "ordinary_return_or_refund_question", "medium")

    if _contains_any(
        normalized_query,
        (
            "delivery",
            "shipping",
            "tracking",
            "standard delivery",
            "express delivery",
            "remote area",
            "public holiday delivery",
            "where is my package",
        ),
    ):
        return _decision(PolicyCategory.DELIVERY, "ordinary_delivery_question", "medium")

    if _contains_any(
        normalized_query,
        (
            "cancel my order",
            "cancel an order",
            "before dispatch",
            "change my address",
            "edit my order",
            "change my order",
            "track my order",
            "order status",
        ),
    ):
        return _decision(PolicyCategory.ORDER, "ordinary_order_question", "medium")

    if _contains_any(
        normalized_query,
        (
            "log in",
            "login",
            "password reset",
            "reset my password",
            "verify my email",
            "verify my phone",
            "account access",
        ),
    ):
        return _decision(PolicyCategory.ACCOUNT_SECURITY, "ordinary_account_question", "medium")

    if _contains_any(
        normalized_query,
        (
            "book a flight",
            "book a hotel",
            "medical advice",
            "legal advice",
            "write software",
            "weather forecast",
        ),
    ):
        return _decision(
            PolicyCategory.UNCLEAR,
            "explicit_unsupported_request",
            "low",
            should_escalate=True,
            reason="The request does not match a documented NovaCart support service.",
        )

    return _decision(PolicyCategory.UNCLEAR, "unclear_request", "low")

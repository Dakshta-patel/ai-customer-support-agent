import unittest

from backend.app.policy import PolicyCategory, classify_policy


class PolicyClassificationTests(unittest.TestCase):
    def assert_escalates(self, query: str, category: PolicyCategory, rule: str) -> None:
        decision = classify_policy(query)
        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.policy_category, category)
        self.assertEqual(decision.rule_match, rule)
        self.assertIsNotNone(decision.escalation_reason)
        self.assertTrue(decision.escalation_reason)

    def assert_does_not_escalate(
        self, query: str, category: PolicyCategory, rule: str
    ) -> None:
        decision = classify_policy(query)
        self.assertFalse(decision.should_escalate)
        self.assertIsNone(decision.escalation_reason)
        self.assertEqual(decision.policy_category, category)
        self.assertEqual(decision.rule_match, rule)

    def test_empty_and_whitespace_queries(self) -> None:
        for query in ("", "   ", "\n\t"):
            decision = classify_policy(query)
            self.assertEqual(
                decision,
                classify_policy(query),
            )
            self.assertEqual(decision.policy_category, PolicyCategory.EMPTY)
            self.assertFalse(decision.should_escalate)
            self.assertIsNone(decision.escalation_reason)
            self.assertEqual(decision.rule_match, "empty_query")
            self.assertEqual(decision.confidence, "high")

    def test_ordinary_delivery_question(self) -> None:
        self.assert_does_not_escalate(
            "How long does standard delivery take?",
            PolicyCategory.DELIVERY,
            "ordinary_delivery_question",
        )

    def test_delivery_delay_and_delivered_missing_escalate(self) -> None:
        self.assert_escalates(
            "Tracking stopped beyond the expected window.",
            PolicyCategory.DELIVERY,
            "delivery_exception_requires_review",
        )
        self.assert_escalates(
            "My parcel was marked delivered but is missing.",
            PolicyCategory.DELIVERY,
            "delivery_exception_requires_review",
        )

    def test_ordinary_order_cancellation(self) -> None:
        self.assert_does_not_escalate(
            "Can I cancel my order before dispatch?",
            PolicyCategory.ORDER,
            "ordinary_order_question",
        )

    def test_disputed_cancellation_escalates(self) -> None:
        self.assert_escalates(
            "My cancellation status is wrong.",
            PolicyCategory.ORDER,
            "order_status_or_record_conflict",
        )

    def test_ordinary_refund_question(self) -> None:
        self.assert_does_not_escalate(
            "What is the refund timing?",
            PolicyCategory.REFUND_RETURN,
            "ordinary_return_or_refund_question",
        )

    def test_return_exceptions_escalate(self) -> None:
        self.assert_escalates(
            "Can I get an exception for a return after 30 days?",
            PolicyCategory.REFUND_RETURN,
            "return_or_refund_exception",
        )
        self.assert_escalates(
            "I dispute the return inspection decision.",
            PolicyCategory.REFUND_RETURN,
            "return_or_refund_exception",
        )

    def test_ordinary_account_login(self) -> None:
        self.assert_does_not_escalate(
            "How do I reset my password?",
            PolicyCategory.ACCOUNT_SECURITY,
            "ordinary_account_question",
        )

    def test_account_takeover_and_secret_disclosure_escalate(self) -> None:
        self.assert_escalates(
            "I suspect an account takeover.",
            PolicyCategory.ACCOUNT_SECURITY,
            "account_security_compromise",
        )
        self.assert_escalates(
            "I shared my OTP with someone.",
            PolicyCategory.ACCOUNT_SECURITY,
            "account_security_compromise",
        )

    def test_account_fraud_report_escalates_with_account_security_reason(self) -> None:
        decision = classify_policy("I want to report fraud on my account.")

        self.assertTrue(decision.should_escalate)
        self.assertEqual(decision.policy_category, PolicyCategory.ACCOUNT_SECURITY)
        self.assertEqual(decision.rule_match, "account_security_compromise")
        self.assertEqual(
            decision.escalation_reason,
            "The request involves account security or ownership verification.",
        )

    def test_ordinary_account_question_does_not_escalate(self) -> None:
        self.assert_does_not_escalate(
            "How do I reset my password?",
            PolicyCategory.ACCOUNT_SECURITY,
            "ordinary_account_question",
        )

    def test_ordinary_payment_failure(self) -> None:
        self.assert_does_not_escalate(
            "Why did my payment fail?",
            PolicyCategory.PAYMENT,
            "ordinary_payment_question",
        )

    def test_payment_fraud_duplicate_and_missing_order_escalate(self) -> None:
        for query in (
            "I suspect payment fraud.",
            "I see a duplicate payment.",
            "Money was deducted but there is no order.",
        ):
            decision = classify_policy(query)
            self.assertTrue(decision.should_escalate)
            self.assertEqual(decision.policy_category, PolicyCategory.PAYMENT)
            self.assertEqual(decision.rule_match, "high_risk_payment_issue")
            self.assertTrue(decision.escalation_reason)

    def test_explicit_human_agent_request_escalates(self) -> None:
        self.assert_escalates(
            "I need a support agent.",
            PolicyCategory.HUMAN_SUPPORT,
            "explicit_human_support_request",
        )

    def test_vague_request_is_unclear_without_escalation(self) -> None:
        self.assert_does_not_escalate(
            "I need help.",
            PolicyCategory.UNCLEAR,
            "unclear_request",
        )
        self.assertEqual(classify_policy("I need help.").confidence, "low")

    def test_explicit_unsupported_request_escalates(self) -> None:
        self.assert_escalates(
            "Can NovaCart book a flight?",
            PolicyCategory.UNCLEAR,
            "explicit_unsupported_request",
        )

    def test_precedence_prefers_account_security(self) -> None:
        decision = classify_policy("I cannot access my phone and there is an unfamiliar order")
        self.assertEqual(decision.policy_category, PolicyCategory.ACCOUNT_SECURITY)
        self.assertEqual(decision.rule_match, "account_security_compromise")
        self.assertTrue(decision.should_escalate)

    def test_precedence_prefers_payment_over_order(self) -> None:
        decision = classify_policy("Payment was deducted but no order record exists")
        self.assertEqual(decision.policy_category, PolicyCategory.PAYMENT)
        self.assertEqual(decision.rule_match, "high_risk_payment_issue")
        self.assertTrue(decision.should_escalate)

    def test_classification_is_deterministic_and_normalizes_input(self) -> None:
        first = classify_policy("  WHY DID MY PAYMENT FAIL?  ")
        second = classify_policy("why did my payment fail?")
        self.assertEqual(first, second)
        self.assertEqual(first.policy_category, PolicyCategory.PAYMENT)
        self.assertIsNone(first.escalation_reason)


if __name__ == "__main__":
    unittest.main()

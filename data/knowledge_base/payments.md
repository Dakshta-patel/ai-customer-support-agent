# NovaCart Payments

- **Policy version:** 1.0
- **Effective date:** 2026-09-11
- **Company:** NovaCart
- **Document type:** Payment support policy

## Accepted payment methods

NovaCart accepts eligible:

- Credit and debit cards.
- UPI payments.
- Net banking payments.

Availability can depend on the order, customer location, payment provider, and temporary service conditions.

## Payment security

NovaCart support will never ask for a full card number, CVV, password, or OTP. Customers should enter payment information only in the secure checkout or official payment-provider flow and should not send payment secrets through email or chat.

Support may ask for limited transaction details needed to locate a payment, such as the order ID, approximate payment time, amount, payment method type, or a provider transaction reference. Customers should mask sensitive information when sharing screenshots.

## Payment failures

A payment may fail because of an issuer decline, incorrect or expired payment information, a UPI or net-banking session timeout, provider downtime, insufficient available funds, or a security check. Customers can verify their payment method and try again after confirming that no order was created.

Repeated failed attempts can result in multiple temporary authorization holds. The bank or payment provider controls the release timing for a hold that was not captured by NovaCart.

## Pending payments

A pending status means the payment result has not been fully confirmed. Customers should avoid repeatedly retrying while the status is unresolved. Check for an order confirmation and allow the provider time to update; contact support with the order ID or limited transaction details if the pending state continues.

## Money deducted but no order confirmation

If money appears to have been deducted but no order was confirmed:

1. Do not place repeated orders immediately.
2. Check the account order list and email for a delayed confirmation.
3. Note the payment time, amount, payment method type, and provider transaction reference if available.
4. Contact support at support@novacart.example.
5. Never send a password, OTP, CVV, or full card number.

NovaCart will check whether the payment was captured, only authorized, reversed, or not received. If no order was created and the payment was not captured, the payment provider may need to release or reverse the amount.

## Common questions

### Can I pay with UPI or net banking?

Yes, both are accepted where available, along with eligible credit and debit cards.

### Why did my payment fail but my bank shows a debit?

The amount may be a temporary authorization or a provider-side pending transaction rather than a completed capture. Contact support with limited transaction details if it does not resolve.

### Can support confirm a payment using my OTP?

No. Never share an OTP with support or anyone else.

### Will NovaCart retry a failed payment automatically?

Customers should not assume an automatic retry. Check the order status before trying again and contact support if the payment result is unclear.

## Important limitations

- Payment providers and banks control some authorization, reversal, and posting timelines.
- A bank debit does not by itself prove that an order was successfully created.
- Payment method availability may vary by order and can be temporarily interrupted.

## When to escalate

Escalate suspected duplicate captures, an unexplained debit with no order after the provider's pending period, suspected payment fraud, mismatched payment and order records, or a customer who may have disclosed a payment secret.

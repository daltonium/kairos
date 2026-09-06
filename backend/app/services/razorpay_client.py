"""
backend/app/services/razorpay_client.py
REPLACES the earlier version.
Fix: razorpay-python's verify_signature() internally does
bytes(body, 'utf-8'), which requires `body` to already be a str --
passing raw bytes (as FastAPI's request.body() returns) crashes with
"TypeError: encoding without a string argument". Decode before passing.
"""
import razorpay
from app.core.config import settings

_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(amount_rupees: float, receipt: str) -> dict:
    """Amount must be converted to paise (smallest currency subunit) per Razorpay's API."""
    amount_paise = int(round(amount_rupees * 100))
    return _client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1,
    })


def verify_payment_signature(order_id: str, payment_id: str, signature: str) -> bool:
    try:
        _client.utility.verify_payment_signature({
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        })
        return True
    except razorpay.errors.SignatureVerificationError:
        return False


def verify_webhook_signature(raw_body: bytes, signature: str) -> bool:
    """
    IMPORTANT: uses RAZORPAY_WEBHOOK_SECRET, a SEPARATE secret from your
    API key/secret pair -- configured in the Razorpay Dashboard under
    Webhooks settings. Using the API secret here will always fail.

    razorpay-python's verify_signature() does bytes(body, 'utf-8')
    internally, which requires body to be a str, not bytes -- decode first.
    """
    body_str = raw_body.decode("utf-8") if isinstance(raw_body, bytes) else raw_body
    try:
        _client.utility.verify_webhook_signature(body_str, signature, settings.RAZORPAY_WEBHOOK_SECRET)
        return True
    except razorpay.errors.SignatureVerificationError:
        return False

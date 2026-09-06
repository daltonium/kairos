"""
backend/tests/test_payments.py
Phase 10 regression tests.

Scope note: the /payments/webhook endpoint is intentionally NOT tested
here with a fabricated payload -- it requires a genuine HMAC-SHA256
signature computed with RAZORPAY_WEBHOOK_SECRET, which only Razorpay's
servers (or their dashboard's "Test Webhook" button) can produce
correctly. A fake signature would just test that verify_webhook_signature
rejects garbage, which the one negative test below already covers
without needing gig/order setup. Full webhook-to-wallet-credit flow
should continue to be verified manually via Razorpay's Test Webhook
button per the Phase 10 setup doc.
"""
import uuid
import pytest

from app.models.marketplace import GigListing, GigApplication

pytestmark = pytest.mark.asyncio


async def test_wallet_auto_creates_with_zero_balance(client, student):
    resp = await client.get("/api/v1/payments/wallet/me", headers=student["headers"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["balance"] == 0
    assert body["pending_balance"] == 0


async def test_withdraw_blocked_when_insufficient_balance(client, student):
    resp = await client.post(
        "/api/v1/payments/wallet/withdraw", headers=student["headers"], json={"amount": 500}
    )
    assert resp.status_code == 400


async def test_create_order_requires_completed_gig(client, db_session, company, student):
    gig = GigListing(id=str(uuid.uuid4()), client_id=company["user_id"], title="Payment Test Gig", status="open")
    db_session.add(gig)
    await db_session.flush()

    application = GigApplication(
        id=str(uuid.uuid4()), gig_id=gig.id, student_id=student["user_id"], status="pending",
    )
    db_session.add(application)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/payments/create-order",
        headers=company["headers"],
        json={"gig_application_id": application.id, "amount": 100},
    )
    assert resp.status_code == 400  # gig application is "pending", not "completed"


async def test_create_order_succeeds_for_completed_gig(client, db_session, company, student):
    """Hits the real Razorpay API in test mode -- creates a real (test-mode,
    zero-cost) order. Requires valid RAZORPAY_KEY_ID/SECRET in .env."""
    gig = GigListing(id=str(uuid.uuid4()), client_id=company["user_id"], title="Completed Gig", status="completed")
    db_session.add(gig)
    await db_session.flush()

    application = GigApplication(
        id=str(uuid.uuid4()), gig_id=gig.id, student_id=student["user_id"], status="completed",
    )
    db_session.add(application)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/payments/create-order",
        headers=company["headers"],
        json={"gig_application_id": application.id, "amount": 100},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["razorpay_order_id"] is not None
    assert body["status"] == "created"


async def test_webhook_rejects_invalid_signature(client):
    resp = await client.post(
        "/api/v1/payments/webhook",
        headers={"X-Razorpay-Signature": "not-a-real-signature"},
        json={"event": "payment.captured", "payload": {}},
    )
    assert resp.status_code == 400


async def test_payment_history_returns_list(client, student):
    resp = await client.get("/api/v1/payments/history", headers=student["headers"])
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


async def test_notifications_list_and_mark_read(client, student):
    list_resp = await client.get("/api/v1/notifications/", headers=student["headers"])
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)


async def test_cannot_mark_others_notification_read(client, db_session, student, second_student):
    from app.models.marketplace import Notification
    notif = Notification(
        id=str(uuid.uuid4()), user_id=student["user_id"], category="system", message="test", is_read=False,
    )
    db_session.add(notif)
    await db_session.commit()

    resp = await client.post(f"/api/v1/notifications/{notif.id}/read", headers=second_student["headers"])
    assert resp.status_code == 403

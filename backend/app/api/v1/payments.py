"""
backend/app/api/v1/payments.py
REPLACES the Phase 2 stub.
Razorpay order creation + webhook handling + wallet.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.user import User
from app.models.marketplace import GigApplication, GigListing, Payment, Wallet
from app.schemas.payments import CreatePayoutRequest, PaymentResponse, WalletResponse, WithdrawRequest
from app.services.razorpay_client import create_order, verify_webhook_signature
from app.services.notifications import create_notification
from app.services.email import send_payment_received_email

router = APIRouter()


@router.get("/ping")
async def ping():
    return {"router": "payments", "status": "ok"}


async def _get_or_create_wallet(db: AsyncSession, user_id: str) -> Wallet:
    result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
    wallet = result.scalar_one_or_none()
    if wallet is None:
        wallet = Wallet(id=str(uuid.uuid4()), user_id=user_id, balance=0, pending_balance=0)
        db.add(wallet)
        await db.commit()
        await db.refresh(wallet)
    return wallet


@router.post("/create-order", response_model=PaymentResponse, status_code=201)
async def create_payment_order(
    payload: CreatePayoutRequest,
    current_user: User = Depends(get_current_user),  # client initiates payment for a completed gig
    db: AsyncSession = Depends(get_db),
):
    app_result = await db.execute(select(GigApplication).where(GigApplication.id == payload.gig_application_id))
    application = app_result.scalar_one_or_none()
    if application is None:
        raise HTTPException(status_code=404, detail="Gig application not found")
    if application.status != "completed":
        raise HTTPException(status_code=400, detail="Gig must be completed before payment")

    order = create_order(payload.amount, receipt=f"gig-{application.id}")

    payment = Payment(
        id=str(uuid.uuid4()),
        user_id=application.student_id,
        gig_application_id=application.id,
        razorpay_order_id=order["id"],
        amount=payload.amount,
        status="created",
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


@router.post("/webhook")
async def razorpay_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Razorpay sends events here on payment completion/failure. Signature MUST
    be verified against the RAW request body using the webhook secret
    (separate from your API key/secret) -- never trust the payload otherwise.
    """
    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")

    if not verify_webhook_signature(raw_body, signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")

    if event == "payment.captured":
        razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        razorpay_payment_id = payload["payload"]["payment"]["entity"]["id"]

        result = await db.execute(select(Payment).where(Payment.razorpay_order_id == razorpay_order_id))
        payment = result.scalar_one_or_none()
        if payment is not None:
            payment.status = "captured"
            payment.razorpay_payment_id = razorpay_payment_id
            wallet = await _get_or_create_wallet(db, payment.user_id)
            wallet.balance += float(payment.amount)
            await db.commit()

            student_result = await db.execute(select(User).where(User.id == payment.user_id))
            student = student_result.scalar_one_or_none()
            gig_title = "your gig"
            if payment.gig_application_id:
                app_result = await db.execute(
                    select(GigApplication).where(GigApplication.id == payment.gig_application_id)
                )
                app_row = app_result.scalar_one_or_none()
                if app_row:
                    gig_result = await db.execute(select(GigListing).where(GigListing.id == app_row.gig_id))
                    gig_row = gig_result.scalar_one_or_none()
                    if gig_row:
                        gig_title = gig_row.title

            if student:
                await create_notification(
                    db, student.id, "payments", f"Payment of Rs. {payment.amount} received for {gig_title}."
                )
                await send_payment_received_email(student.email, float(payment.amount), gig_title)

    elif event == "payment.failed":
        razorpay_order_id = payload["payload"]["payment"]["entity"]["order_id"]
        result = await db.execute(select(Payment).where(Payment.razorpay_order_id == razorpay_order_id))
        payment = result.scalar_one_or_none()
        if payment is not None:
            payment.status = "failed"
            await db.commit()

    return {"status": "ok"}


@router.get("/wallet/me", response_model=WalletResponse)
async def get_my_wallet(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(db, current_user.id)
    return wallet


@router.post("/wallet/withdraw", response_model=WalletResponse)
async def withdraw_from_wallet(
    payload: WithdrawRequest,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db),
):
    wallet = await _get_or_create_wallet(db, current_user.id)
    if payload.amount > float(wallet.balance):
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # NOTE: actual payout to a bank account/UPI requires Razorpay Payouts/
    # RazorpayX, a separate product from standard Checkout -- this endpoint
    # only moves the amount from balance to pending_balance as a placeholder
    # for that integration.
    wallet.balance -= payload.amount
    wallet.pending_balance += payload.amount
    await db.commit()
    await db.refresh(wallet)
    return wallet


@router.get("/history", response_model=list[PaymentResponse])
async def payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Payment).where(Payment.user_id == current_user.id))
    return result.scalars().all()

"""
backend/app/services/email.py
Transactional email via Resend. Uses httpx.AsyncClient directly rather
than the sync `resend` SDK, since the SDK's send() call would block the
FastAPI event loop inside async route handlers.
"""
import httpx
from app.core.config import settings

RESEND_URL = "https://api.resend.com/emails"
FROM_ADDRESS = "Kairos <onboarding@resend.dev>"  # replace with your verified domain sender once set up


async def send_email(to: str, subject: str, html: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                RESEND_URL,
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
                json={"from": FROM_ADDRESS, "to": [to], "subject": subject, "html": html},
            )
        return resp.status_code in (200, 201)
    except httpx.HTTPError:
        return False


async def send_welcome_email(to: str, full_name: str) -> bool:
    return await send_email(
        to, "Welcome to Kairos",
        f"<p>Hi {full_name},</p><p>Welcome to Kairos — let's build your career.</p>",
    )


async def send_gig_accepted_email(to: str, gig_title: str) -> bool:
    return await send_email(
        to, "Your gig application was accepted",
        f"<p>Good news — your application for <b>{gig_title}</b> was accepted. Log in to get started.</p>",
    )


async def send_payment_received_email(to: str, amount: float, gig_title: str) -> bool:
    return await send_email(
        to, "Payment received",
        f"<p>You've received a payment of <b>Rs. {amount:.2f}</b> for completing <b>{gig_title}</b>.</p>",
    )

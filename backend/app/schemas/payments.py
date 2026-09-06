"""
backend/app/schemas/payments.py
"""
from typing import Optional
from pydantic import BaseModel, Field


class CreatePayoutRequest(BaseModel):
    gig_application_id: str
    amount: float = Field(gt=0)


class PaymentResponse(BaseModel):
    id: str
    user_id: str
    gig_application_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: float
    status: str

    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    balance: float
    pending_balance: float

    class Config:
        from_attributes = True


class WithdrawRequest(BaseModel):
    amount: float = Field(gt=0)

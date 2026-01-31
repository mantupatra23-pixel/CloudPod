import os
import hmac
import hashlib
import stripe
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime

from app.db import SessionLocal
from app.wallet import credit
from app.models import Base

# ==================================================
# ROUTER
# ==================================================
router = APIRouter(prefix="/payment", tags=["Payment"])


# ==================================================
# DB DEPENDENCY
# ==================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================================================
# PAYMENT LOG (IDEMPOTENCY TABLE)
# ==================================================
class PaymentLog(Base):
    __tablename__ = "payment_logs"

    id = Column(Integer, primary_key=True)
    provider = Column(String, index=True)          # razorpay / stripe
    reference_id = Column(String, unique=True)     # payment_id / session_id
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# RAZORPAY SIGNATURE VERIFY
# ==================================================
def verify_razorpay_signature(body: bytes, signature: str) -> bool:
    secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
    if not secret:
        return False

    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


# ==================================================
# RAZORPAY WEBHOOK (UPI / INDIA)
# ==================================================
@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    body = await request.body()
    payload = await request.json()

    signature = request.headers.get("X-Razorpay-Signature")
    if not signature or not verify_razorpay_signature(body, signature):
        return {"error": "invalid signature"}

    # only successful payments
    if payload.get("event") != "payment.captured":
        return {"status": "ignored"}

    entity = payload["payload"]["payment"]["entity"]

    payment_id = entity["id"]
    amount = entity["amount"] / 100          # paise → rupees
    user_id = entity.get("notes", {}).get("user_id")

    if not user_id:
        return {"error": "user_id missing"}

    # -------- IDEMPOTENCY CHECK --------
    exists = db.query(PaymentLog).filter_by(
        provider="razorpay",
        reference_id=payment_id
    ).first()

    if exists:
        return {"status": "already processed"}

    # wallet credit
    credit(
        db=db,
        user_id=int(user_id),
        amount=amount,
        reason=f"UPI Payment (Razorpay {payment_id})"
    )

    # save payment log
    db.add(PaymentLog(
        provider="razorpay",
        reference_id=payment_id
    ))
    db.commit()

    return {"status": "wallet credited"}


# ==================================================
# STRIPE WEBHOOK (GLOBAL + VERIFIED)
# ==================================================
@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    sig = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig,
            secret=os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except Exception:
        return {"error": "invalid signature"}

    # only successful checkout
    if event["type"] != "checkout.session.completed":
        return {"status": "ignored"}

    session = event["data"]["object"]

    payment_id = session["id"]
    amount = session["amount_total"] / 100   # cents → currency
    user_id = session.get("metadata", {}).get("user_id")

    if not user_id:
        return {"error": "user_id missing"}

    # -------- IDEMPOTENCY CHECK --------
    exists = db.query(PaymentLog).filter_by(
        provider="stripe",
        reference_id=payment_id
    ).first()

    if exists:
        return {"status": "already processed"}

    # wallet credit
    credit(
        db=db,
        user_id=int(user_id),
        amount=amount,
        reason=f"Stripe Payment ({payment_id})"
    )

    # save payment log
    db.add(PaymentLog(
        provider="stripe",
        reference_id=payment_id
    ))
    db.commit()

    return {"status": "wallet credited"}

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.db import SessionLocal
from app.models import User, WalletTransaction
from app.payments import PaymentLog
from app.admin_auth import admin_auth

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(admin_auth)]
)

# ======================
# DB DEPENDENCY
# ======================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ======================
# REVENUE SUMMARY
# ======================
@router.get("/revenue")
def revenue(db: Session = Depends(get_db)):
    total = (
        db.query(func.sum(WalletTransaction.amount))
        .filter(WalletTransaction.amount > 0)
        .scalar()
    ) or 0

    return {"total_revenue": float(total)}


# ======================
# PAYMENTS LIST
# ======================
@router.get("/payments")
def payments(db: Session = Depends(get_db)):
    return (
        db.query(PaymentLog)
        .order_by(PaymentLog.created_at.desc())
        .limit(100)
        .all()
    )


# ======================
# WALLET TRANSACTIONS
# ======================
@router.get("/wallet-transactions")
def wallet_transactions(db: Session = Depends(get_db)):
    return (
        db.query(WalletTransaction)
        .order_by(WalletTransaction.created_at.desc())
        .limit(100)
        .all()
    )


# ======================
# USER BALANCES
# ======================
@router.get("/users")
def users(db: Session = Depends(get_db)):
    return (
        db.query(
            User.id,
            User.email,
            User.wallet_balance,
            User.is_active
        )
        .order_by(User.id.desc())
        .all()
    )


# ======================
# MANUAL WALLET CREDIT / DEBIT
# ======================
@router.post("/wallet-adjust")
def wallet_adjust(
    user_id: int,
    amount: float,
    reason: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.wallet_balance += amount

    txn = WalletTransaction(
        user_id=user.id,
        amount=amount,
        description=f"Admin: {reason}",
        created_at=datetime.utcnow()
    )

    db.add(txn)
    db.commit()

    return {"status": "success", "new_balance": user.wallet_balance}


# ======================
# USER BLOCK / UNBLOCK
# ======================
@router.post("/user-status")
def set_user_status(
    user_id: int,
    active: bool,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = active
    db.commit()

    return {
        "user_id": user.id,
        "active": user.is_active
    }


# ======================
# REFUND MARK (MANUAL / GATEWAY)
# ======================
@router.post("/refund")
def refund_payment(
    payment_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    payment = db.query(PaymentLog).filter(PaymentLog.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.refunded:
        raise HTTPException(status_code=400, detail="Already refunded")

    payment.refunded = True
    payment.refund_reason = reason
    payment.refunded_at = datetime.utcnow()

    db.commit()
    return {"status": "refunded"}


# ======================
# CPU / GPU USAGE STATS
# ======================
@router.get("/usage")
def usage_stats(db: Session = Depends(get_db)):
    cpu = (
        db.query(func.sum(WalletTransaction.minutes))
        .filter(WalletTransaction.resource == "cpu")
        .scalar()
    ) or 0

    gpu = (
        db.query(func.sum(WalletTransaction.minutes))
        .filter(WalletTransaction.resource == "gpu")
        .scalar()
    ) or 0

    return {
        "cpu_minutes": cpu,
        "gpu_minutes": gpu
    }


# ======================
# SYSTEM HEALTH (STATIC)
# ======================
@router.get("/health")
def health():
    return {
        "backend": "ok",
        "cpu_nodes": "online",
        "gpu_nodes": "online"
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import SessionLocal
from app.models import User, WalletTransaction, Payments
from app.admin_auth import admin_auth

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(admin_auth)]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# REVENUE SUMMARY
# =========================
@router.get("/revenue")
def revenue(db: Session = Depends(get_db)):
    total = db.query(func.sum(WalletTransaction.amount)).filter(
        WalletTransaction.amount > 0
    ).scalar() or 0

    return {
        "total_revenue": total
    }

# =========================
# PAYMENTS LIST
# =========================
@router.get("/payments")
def payments(db: Session = Depends(get_db)):
    rows = db.query(Payments).order_by(Payments.created_at.desc()).limit(100).all()
    return rows

# =========================
# WALLET TRANSACTIONS
# =========================
@router.get("/wallet-transactions")
def wallet_transactions(db: Session = Depends(get_db)):
    rows = (
        db.query(WalletTransaction)
        .order_by(WalletTransaction.created_at.desc())
        .limit(100)
        .all()
    )
    return rows

# =========================
# USER BALANCES
# =========================
@router.get("/users")
def users(db: Session = Depends(get_db)):
    users = db.query(User.id, User.email, User.wallet).all()
    return users

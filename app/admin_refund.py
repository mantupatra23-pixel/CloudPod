from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.wallet import credit
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

@router.post("/refund")
def refund(user_id: int, amount: float, db: Session = Depends(get_db)):
    credit(db, user_id, amount, "Admin Refund")
    return {
        "status": "refunded",
        "user_id": user_id,
        "amount": amount
    }

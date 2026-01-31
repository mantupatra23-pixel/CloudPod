from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Subscription, Plan
from app.deps import get_current_user
from app.wallet import debit

router = APIRouter(prefix="/subscription", tags=["Subscription"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/plans")
def list_plans(db: Session = Depends(get_db)):
    return db.query(Plan).all()

@router.post("/subscribe")
def subscribe(
    plan_id: int,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404)

    # charge monthly fee
    if plan.monthly_price > 0:
        ok = debit(db, user_id, plan.monthly_price, f"Subscription {plan.name}")
        if not ok:
            raise HTTPException(status_code=400, detail="Insufficient balance")

    expires = datetime.utcnow() + timedelta(days=30)

    db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.active == True
    ).update({"active": False})

    sub = Subscription(
        user_id=user_id,
        plan_id=plan.id,
        active=True,
        expires_at=expires
    )
    db.add(sub)
    db.commit()

    return {"status": "subscribed", "plan": plan.name}

@router.get("/current")
def current_subscription(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Subscription).filter(
        Subscription.user_id == user_id,
        Subscription.active == True
    ).first()

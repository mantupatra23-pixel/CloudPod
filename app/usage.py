from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import SessionLocal
from app.models import Usage
from app.deps import get_current_user

router = APIRouter(prefix="/usage", tags=["Usage"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# FULL USAGE HISTORY
# =========================
@router.get("")
def usage_history(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = (
        db.query(Usage)
        .filter(Usage.user_id == user_id)
        .order_by(Usage.created_at.desc())
        .all()
    )
    return rows

# =========================
# USAGE SUMMARY
# =========================
@router.get("/summary")
def usage_summary(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    total = db.query(func.sum(Usage.cost)).filter(
        Usage.user_id == user_id
    ).scalar() or 0

    cpu = db.query(func.sum(Usage.cost)).filter(
        Usage.user_id == user_id,
        Usage.resource == "cpu"
    ).scalar() or 0

    gpu = db.query(func.sum(Usage.cost)).filter(
        Usage.user_id == user_id,
        Usage.resource == "gpu"
    ).scalar() or 0

    return {
        "total_spent": total,
        "cpu_spent": cpu,
        "gpu_spent": gpu
    }

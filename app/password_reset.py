import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User, PasswordReset
from app.auth import hash_password
from app.email_service import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# FORGOT PASSWORD
# =========================
@router.post("/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"status": "ok"}  # avoid email enumeration

    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(minutes=15)

    db.add(
        PasswordReset(
            user_id=user.id,
            token=token,
            expires_at=expires
        )
    )
    db.commit()

    reset_link = f"https://cloudpod.app/reset-password?token={token}"

    send_email(
        to=user.email,
        subject="CloudPod Password Reset",
        body=f"Reset your password:\n\n{reset_link}\n\nLink valid for 15 minutes."
    )

    return {"status": "reset link sent"}

# =========================
# RESET PASSWORD
# =========================
@router.post("/reset-password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    record = (
        db.query(PasswordReset)
        .filter(PasswordReset.token == token)
        .first()
    )

    if not record or record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == record.user_id).first()
    user.password = hash_password(new_password)

    db.delete(record)
    db.commit()

    return {"status": "password updated"}

import secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import APIKey
from app.deps import get_current_user

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_key():
    return "cp_" + secrets.token_hex(24)

@router.post("/create")
def create_key(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    key = generate_key()
    db.add(APIKey(user_id=user_id, key=key))
    db.commit()
    return {"api_key": key}

@router.get("")
def list_keys(
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(APIKey).filter(
        APIKey.user_id == user_id
    ).all()

@router.post("/revoke")
def revoke_key(
    key: str,
    user_id: int = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    row = db.query(APIKey).filter(
        APIKey.key == key,
        APIKey.user_id == user_id
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key not found")
    row.active = False
    db.commit()
    return {"status": "revoked"}

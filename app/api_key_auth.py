from fastapi import Header, HTTPException
from app.db import SessionLocal
from app.models import APIKey

def get_user_from_api_key(x_api_key: str = Header(...)):
    db = SessionLocal()
    try:
        row = db.query(APIKey).filter(
            APIKey.key == x_api_key,
            APIKey.active == True
        ).first()
        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return row.user_id
    finally:
        db.close()

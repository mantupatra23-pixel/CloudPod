from fastapi import Depends, Header, HTTPException
from app.auth import decode_token

def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401)

    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        return payload["user_id"]
    except Exception:
        raise HTTPException(status_code=401)

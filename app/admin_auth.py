import os
from fastapi import Header, HTTPException

def admin_auth(x_admin_secret: str = Header(...)):
    if x_admin_secret != os.getenv("ADMIN_SECRET"):
        raise HTTPException(status_code=401, detail="Unauthorized")

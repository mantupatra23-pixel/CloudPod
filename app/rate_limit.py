import time
from fastapi import HTTPException
from app.redis_client import r

def rate_limit(key: str, limit: int, window: int):
    now = int(time.time())
    redis_key = f"rate:{key}:{now // window}"

    count = r.incr(redis_key)
    if count == 1:
        r.expire(redis_key, window)

    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )

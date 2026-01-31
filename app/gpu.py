import time
from fastapi import APIRouter, Depends

from app.redis_client import r
from app.db import SessionLocal
from app.wallet import debit
from app.models import Usage
from app.docker_gpu_client import gpu_docker_run, gpu_docker_stop
from app.deps import get_current_user
from app.api_key_auth import get_user_from_api_key
from app.rate_limit import rate_limit
from app.pricing_engine import resolve_price

router = APIRouter(prefix="/gpu", tags=["GPU"])

# ==================================================
# DB DEPENDENCY
# ==================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================================================
# INTERNAL START LOGIC
# ==================================================
def _start_gpu(user_id: int):
    # GPU stricter rate limit
    rate_limit(f"gpu_start:{user_id}", limit=3, window=60)

    key = f"gpu:{user_id}"

    if r.hget(key, "running") == "1":
        return {"error": "GPU already running"}

    container_name = f"cloudpod-gpu-{user_id}"
    gpu_docker_run(container_name)

    r.hset(
        key,
        mapping={
            "start": int(time.time()),
            "running": 1,
            "container": container_name,
        },
    )

    return {
        "status": "GPU started",
        "container": container_name,
        "billing": "per-minute",
    }


# ==================================================
# INTERNAL STOP LOGIC (BILLING)
# ==================================================
def _stop_gpu(user_id: int, db):
    key = f"gpu:{user_id}"
    data = r.hgetall(key)

    if not data or data.get("running") != "1":
        return {"error": "GPU not running"}

    container = data.get("container")
    if container:
        gpu_docker_stop(container)

    start_time = int(data.get("start", 0))
    seconds = int(time.time()) - start_time
    minutes = max(1, seconds // 60)

    # 🔥 PLAN / SUBSCRIPTION AWARE PRICING
    price_per_min = resolve_price(user_id, "gpu")
    cost = minutes * price_per_min

    ok = debit(db, user_id, cost, f"GPU usage {minutes} min")
    r.delete(key)

    if not ok:
        return {
            "error": "insufficient balance",
            "minutes": minutes,
            "cost": cost,
        }

    # save usage
    db.add(
        Usage(
            user_id=user_id,
            resource="gpu",
            minutes=minutes,
            cost=cost,
        )
    )
    db.commit()

    return {
        "status": "GPU stopped",
        "minutes": minutes,
        "cost": cost,
    }


# ==================================================
# UI AUTH ENDPOINTS
# ==================================================
@router.post("/start")
def start_gpu(
    user_id: int = Depends(get_current_user),
):
    return _start_gpu(user_id)


@router.post("/stop")
def stop_gpu(
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    return _stop_gpu(user_id, db)


# ==================================================
# API KEY ENDPOINTS (SDK / AUTOMATION)
# ==================================================
@router.post("/api/start")
def start_gpu_api(
    user_id: int = Depends(get_user_from_api_key),
):
    return _start_gpu(user_id)


@router.post("/api/stop")
def stop_gpu_api(
    user_id: int = Depends(get_user_from_api_key),
    db=Depends(get_db),
):
    return _stop_gpu(user_id, db)

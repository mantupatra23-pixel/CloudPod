import time
from fastapi import APIRouter, Depends

from app.redis_client import r
from app.db import SessionLocal
from app.wallet import debit
from app.models import Usage
from app.docker_client import docker_run, docker_stop
from app.deps import get_current_user
from app.api_key_auth import get_user_from_api_key
from app.rate_limit import rate_limit
from app.pricing_engine import resolve_price

router = APIRouter(prefix="/cpu", tags=["CPU"])

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
def _start_cpu(user_id: int):
    # rate limit: 5 starts / minute / user
    rate_limit(f"cpu_start:{user_id}", limit=5, window=60)

    key = f"cpu:{user_id}"

    if r.hget(key, "running") == "1":
        return {"error": "CPU already running"}

    container_name = f"cloudpod-cpu-{user_id}"
    docker_run(container_name)

    r.hset(
        key,
        mapping={
            "start": int(time.time()),
            "running": 1,
            "container": container_name,
        },
    )

    return {
        "status": "CPU started",
        "container": container_name,
        "billing": "per-minute",
    }


# ==================================================
# INTERNAL STOP LOGIC (BILLING)
# ==================================================
def _stop_cpu(user_id: int, db):
    key = f"cpu:{user_id}"
    data = r.hgetall(key)

    if not data or data.get("running") != "1":
        return {"error": "CPU not running"}

    container = data.get("container")
    if container:
        docker_stop(container)

    start_time = int(data.get("start", 0))
    seconds = int(time.time()) - start_time
    minutes = max(1, seconds // 60)

    # 🔥 PLAN-AWARE PRICING
    price_per_min = resolve_price(user_id, "cpu")
    cost = minutes * price_per_min

    ok = debit(db, user_id, cost, f"CPU usage {minutes} min")
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
            resource="cpu",
            minutes=minutes,
            cost=cost,
        )
    )
    db.commit()

    return {
        "status": "CPU stopped",
        "minutes": minutes,
        "cost": cost,
    }


# ==================================================
# UI AUTH ENDPOINTS
# ==================================================
@router.post("/start")
def start_cpu(
    user_id: int = Depends(get_current_user),
):
    return _start_cpu(user_id)


@router.post("/stop")
def stop_cpu(
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    return _stop_cpu(user_id, db)


# ==================================================
# API KEY ENDPOINTS (SDK / AUTOMATION)
# ==================================================
@router.post("/api/start")
def start_cpu_api(
    user_id: int = Depends(get_user_from_api_key),
):
    return _start_cpu(user_id)


@router.post("/api/stop")
def stop_cpu_api(
    user_id: int = Depends(get_user_from_api_key),
    db=Depends(get_db),
):
    return _stop_cpu(user_id, db)

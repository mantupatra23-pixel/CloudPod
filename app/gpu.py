import time
from fastapi import APIRouter, Depends

from app.redis_client import r
from app.pricing import GPU_PRICE_PER_MIN
from app.db import SessionLocal
from app.wallet import debit
from app.docker_gpu_client import gpu_docker_run, gpu_docker_stop
from app.deps import get_current_user   # ✅ AUTH DEPENDENCY

router = APIRouter(prefix="/gpu", tags=["GPU"])


# =========================
# DB DEPENDENCY
# =========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================
# START GPU (AUTH + DOCKER)
# =========================
@router.post("/start")
def start_gpu(
    user_id: int = Depends(get_current_user)
):
    key = f"gpu:{user_id}"

    # already running check
    if r.hget(key, "running") == "1":
        return {"error": "GPU already running"}

    container_name = f"cloudpod-gpu-{user_id}"

    # start gpu container
    gpu_docker_run(container_name)

    # store session in redis
    r.hset(
        key,
        mapping={
            "start": int(time.time()),
            "running": 1,
            "container": container_name,
        }
    )

    return {
        "status": "GPU started",
        "container": container_name,
        "billing": "per-minute",
    }


# =========================
# STOP GPU (AUTH + DOCKER)
# =========================
@router.post("/stop")
def stop_gpu(
    user_id: int = Depends(get_current_user),
    db=Depends(get_db)
):
    key = f"gpu:{user_id}"
    data = r.hgetall(key)

    if not data or data.get("running") != "1":
        return {"error": "GPU not running"}

    container = data.get("container")

    # stop gpu container
    if container:
        gpu_docker_stop(container)

    # calculate usage
    start_time = int(data.get("start", 0))
    seconds = int(time.time()) - start_time
    minutes = max(1, seconds // 60)

    cost = minutes * GPU_PRICE_PER_MIN

    # debit wallet
    ok = debit(db, user_id, cost, f"GPU usage {minutes} min")

    # clear redis
    r.delete(key)

    if not ok:
        return {
            "error": "insufficient balance",
            "minutes": minutes,
            "cost": cost,
        }

    return {
        "status": "GPU stopped",
        "minutes": minutes,
        "cost": cost,
    }

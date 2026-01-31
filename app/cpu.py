import time
from fastapi import APIRouter, Depends

from app.redis_client import r
from app.pricing import CPU_PRICE_PER_MIN
from app.db import SessionLocal
from app.wallet import debit
from app.models import Usage
from app.docker_client import docker_run, docker_stop
from app.deps import get_current_user

router = APIRouter(prefix="/cpu", tags=["CPU"])


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
# START CPU (AUTH + DOCKER)
# =========================
@router.post("/start")
def start_cpu(
    user_id: int = Depends(get_current_user),
):
    key = f"cpu:{user_id}"

    # already running check
    if r.hget(key, "running") == "1":
        return {"error": "CPU already running"}

    container_name = f"cloudpod-cpu-{user_id}"

    # start docker container
    docker_run(container_name)

    # store session in redis
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


# =========================
# STOP CPU (AUTH + DOCKER)
# =========================
@router.post("/stop")
def stop_cpu(
    user_id: int = Depends(get_current_user),
    db=Depends(get_db),
):
    key = f"cpu:{user_id}"
    data = r.hgetall(key)

    if not data or data.get("running") != "1":
        return {"error": "CPU not running"}

    container = data.get("container")

    # stop docker container
    if container:
        docker_stop(container)

    # calculate usage
    start_time = int(data.get("start", 0))
    seconds = int(time.time()) - start_time
    minutes = max(1, seconds // 60)

    cost = minutes * CPU_PRICE_PER_MIN

    # debit wallet
    ok = debit(db, user_id, cost, f"CPU usage {minutes} min")

    # clear redis
    r.delete(key)

    if not ok:
        return {
            "error": "insufficient balance",
            "minutes": minutes,
            "cost": cost,
        }

    # =========================
    # SAVE USAGE (✅ THIS PART YOU ASKED)
    # =========================
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

import time
import traceback

from app.redis_client import r
from app.pricing import CPU_PRICE_PER_MIN, GPU_PRICE_PER_MIN
from app.db import SessionLocal
from app.wallet import debit
from app.docker_client import docker_stop
from app.logger import logger


BILL_INTERVAL = 60  # seconds
LOCK_TTL = 55       # redis lock ttl


# ============================
# INTERNAL: REDIS LOCK
# ============================
def acquire_lock(lock_key: str) -> bool:
    return r.set(lock_key, "1", nx=True, ex=LOCK_TTL)


# ============================
# CPU AUTO BILLING LOOP
# ============================
def cpu_billing_loop():
    logger.info("[BILLER] CPU billing loop started")

    while True:
        try:
            keys = r.keys("cpu:*")

            for key in keys:
                data = r.hgetall(key)
                if not data or data.get("running") != "1":
                    continue

                lock_key = f"lock:{key}"
                if not acquire_lock(lock_key):
                    continue  # already billed this minute

                try:
                    user_id = int(key.split(":")[1])
                except Exception:
                    r.delete(lock_key)
                    continue

                db = SessionLocal()
                try:
                    ok = debit(
                        db,
                        user_id,
                        CPU_PRICE_PER_MIN,
                        "CPU auto billing (1 min)"
                    )
                finally:
                    db.close()

                if not ok:
                    container = data.get("container")
                    if container:
                        docker_stop(container)

                    r.delete(key)
                    logger.warning(
                        "[BILLER] CPU auto-stopped (low balance) user=%s",
                        user_id
                    )

        except Exception:
            logger.error(
                "[BILLER] CPU billing loop error\n%s",
                traceback.format_exc()
            )

        time.sleep(BILL_INTERVAL)


# ============================
# GPU AUTO BILLING LOOP
# ============================
# NOTE:
# Render backend par GPU/Docker calls allowed nahi
# Actual GPU stop AWS GPU node agent karega
def gpu_billing_loop():
    logger.info("[BILLER] GPU billing loop started")

    while True:
        try:
            keys = r.keys("gpu:*")

            for key in keys:
                data = r.hgetall(key)
                if not data or data.get("running") != "1":
                    continue

                lock_key = f"lock:{key}"
                if not acquire_lock(lock_key):
                    continue

                try:
                    user_id = int(key.split(":")[1])
                except Exception:
                    r.delete(lock_key)
                    continue

                db = SessionLocal()
                try:
                    ok = debit(
                        db,
                        user_id,
                        GPU_PRICE_PER_MIN,
                        "GPU auto billing (1 min)"
                    )
                finally:
                    db.close()

                if not ok:
                    # GPU stop handled by AWS agent
                    r.delete(key)
                    logger.warning(
                        "[BILLER] GPU billing stopped (low balance) user=%s",
                        user_id
                    )

        except Exception:
            logger.error(
                "[BILLER] GPU billing loop error\n%s",
                traceback.format_exc()
            )

        time.sleep(BILL_INTERVAL)

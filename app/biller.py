import time
from app.redis_client import r
from app.pricing import CPU_PRICE_PER_MIN, GPU_PRICE_PER_MIN
from app.db import SessionLocal
from app.wallet import debit
from app.docker_client import docker_stop, gpu_docker_stop


# =========================
# CPU AUTO BILLING LOOP
# =========================
def cpu_billing_loop():
    while True:
        keys = r.keys("cpu:*")

        for key in keys:
            data = r.hgetall(key)
            if not data or data.get("running") != "1":
                continue

            try:
                user_id = int(key.split(":")[1])
            except Exception:
                continue

            db = SessionLocal()
            ok = debit(
                db,
                user_id,
                CPU_PRICE_PER_MIN,
                "CPU auto billing (1 min)"
            )
            db.close()

            if not ok:
                # auto stop on low balance
                container = data.get("container")
                if container:
                    docker_stop(container)

                r.delete(key)
                print(f"[BILLER] CPU auto-stopped for user {user_id}")

        time.sleep(60)  # every minute


# =========================
# GPU AUTO BILLING LOOP
# =========================
def gpu_billing_loop():
    while True:
        keys = r.keys("gpu:*")

        for key in keys:
            data = r.hgetall(key)
            if not data or data.get("running") != "1":
                continue

            try:
                user_id = int(key.split(":")[1])
            except Exception:
                continue

            db = SessionLocal()
            ok = debit(
                db,
                user_id,
                GPU_PRICE_PER_MIN,
                "GPU auto billing (1 min)"
            )
            db.close()

            if not ok:
                # auto stop GPU on low balance
                container = data.get("container")
                if container:
                    gpu_docker_stop(container)

                r.delete(key)
                print(f"[BILLER] GPU auto-stopped for user {user_id}")

        time.sleep(60)  # every minute

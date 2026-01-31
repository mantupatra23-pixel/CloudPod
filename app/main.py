import threading

from fastapi import FastAPI

# =========================
# DATABASE
# =========================
from app.db import engine
from app.models import Base
from app.payments import PaymentLog

# =========================
# ROUTERS
# =========================
from app.cpu import router as cpu_router
from app.gpu import router as gpu_router
from app.payments import router as payment_router
from app.admin import router as admin_router
from app.admin_refund import router as refund_router
from app.auth_routes import router as auth_router
from app.usage import router as usage_router

# =========================
# BILLER
# =========================
from app.biller import cpu_billing_loop

# =========================
# WALLET
# =========================
from app.wallet import get_balance


# =========================
# DATABASE INIT
# =========================
Base.metadata.create_all(bind=engine)


# =========================
# FASTAPI APP
# =========================
app = FastAPI(
    title="CloudPod Backend",
    version="1.0.0"
)


# =========================
# START BACKGROUND BILLER
# =========================
@app.on_event("startup")
def start_biller():
    thread = threading.Thread(
        target=cpu_billing_loop,
        daemon=True
    )
    thread.start()


# =========================
# ROUTERS
# =========================
app.include_router(cpu_router)
app.include_router(gpu_router)
app.include_router(payment_router)
app.include_router(admin_router)
app.include_router(refund_router)
app.include_router(auth_router)
app.include_router(usage_router)

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {
        "service": "CloudPod Backend",
        "status": "running"
    }


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# WALLET BALANCE
# =========================
@app.get("/wallet")
def wallet(user_id: int = 1):
    return {"balance": get_balance(user_id)}

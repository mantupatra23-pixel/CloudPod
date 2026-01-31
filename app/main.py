# =========================
# IMPORTS
# =========================
import threading
from fastapi import FastAPI, Request

# =========================
# DATABASE
# =========================
from app.db import engine
from app.models import Base

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
from app.password_reset import router as password_reset_router
from app.api_keys import router as api_keys_router
from app.orgs import router as orgs_router
from app.subscriptions import router as subscription_router

# =========================
# CORE SERVICES
# =========================
from app.biller import cpu_billing_loop
from app.exceptions import global_exception_handler
from app.seed_plans import seed_plans
from app.wallet import get_balance

# =========================
# APP INIT
# =========================
app = FastAPI(
    title="CloudPod Backend",
    version="1.0.0"
)

# =========================
# DATABASE INIT
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# STARTUP TASKS
# =========================
@app.on_event("startup")
def startup_tasks():
    # seed subscription plans
    seed_plans()

    # start background billing thread
    thread = threading.Thread(
        target=cpu_billing_loop,
        daemon=True
    )
    thread.start()

# =========================
# GLOBAL ERROR HANDLER
# =========================
app.add_exception_handler(Exception, global_exception_handler)

# =========================
# ROUTER REGISTRATION
# =========================
app.include_router(auth_router)
app.include_router(password_reset_router)

app.include_router(cpu_router)
app.include_router(gpu_router)

app.include_router(payment_router)
app.include_router(refund_router)

app.include_router(subscription_router)
app.include_router(usage_router)

app.include_router(api_keys_router)
app.include_router(orgs_router)

app.include_router(admin_router)

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
def wallet(user_id: int):
    return {"balance": get_balance(user_id)}

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


# =========================
# USERS TABLE (AUTH READY)
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)   # hashed password
    wallet = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# USAGE TABLE (CPU / GPU)
# =========================
class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    resource = Column(String)        # cpu / gpu
    minutes = Column(Integer)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# WALLET TRANSACTIONS
# =========================
class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)           # +credit / -debit
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# GPU NODES (MULTI-GPU SCALE)
# =========================
class GPUNodes(Base):
    __tablename__ = "gpu_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)            # node name
    ssh_host = Column(String)        # user@ip
    gpu_type = Column(String)        # 4090 / A100
    total_gpu = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# PAYMENTS (IDEMPOTENCY)
# =========================
class Payments(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    gateway = Column(String)         # razorpay / stripe
    payment_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

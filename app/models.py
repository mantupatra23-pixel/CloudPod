from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

# ==================================================
# USERS (AUTH READY)
# ==================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    wallet = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# USAGE (CPU / GPU BILLING LOG)
# ==================================================
class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    resource = Column(String)           # cpu / gpu
    minutes = Column(Integer)
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# WALLET TRANSACTIONS
# ==================================================
class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    amount = Column(Float)              # +credit / -debit
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# GPU NODES (MULTI-GPU SCALE)
# ==================================================
class GPUNode(Base):
    __tablename__ = "gpu_nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)               # node name
    ssh_host = Column(String)           # user@ip
    gpu_type = Column(String)           # 4090 / A100
    total_gpu = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# PAYMENTS (IDEMPOTENCY)
# ==================================================
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    gateway = Column(String)            # stripe / razorpay
    payment_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# PASSWORD RESET TOKENS
# ==================================================
class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime)


# ==================================================
# API KEYS (PROGRAMMATIC ACCESS)
# ==================================================
class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    key = Column(String, unique=True, index=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ==================================================
# ORGANIZATIONS (TEAM ACCOUNTS)
# ==================================================
class Organization(Base):
    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer, index=True)
    wallet = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrgMember(Base):
    __tablename__ = "org_members"

    id = Column(Integer, primary_key=True, index=True)
    org_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    role = Column(String)               # owner / member


# ==================================================
# PLANS (PRICING TIERS)
# ==================================================
class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    monthly_price = Column(Float)
    cpu_price_per_min = Column(Float)
    gpu_price_per_min = Column(Float)
    max_gpu = Column(Integer)
    priority = Column(Integer, default=0)   # higher = better


# ==================================================
# SUBSCRIPTIONS
# ==================================================
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, index=True)
    plan_id = Column(Integer)
    active = Column(Boolean, default=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

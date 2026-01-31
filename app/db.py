import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database URL (env se ya default sqlite)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cloudpod.db")

# SQLite ke liye special args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args
)

# Session
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency (FastAPI ke liye)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
